from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional, require_roles
from app.models import (
    CategoriaReporte,
    EstadoReporte,
    InteraccionReporte,
    NivelAgua,
    Reporte,
    RolUsuario,
    SeveridadBache,
    TipoInteraccion,
    Usuario,
)
from app.schemas.schemas import (
    CambioEstadoIn,
    InteraccionIn,
    PaginatedReportesOut,
    ReporteCreate,
    ReporteOut,
    ReporteUpdateCiudadano,
)
from app.services.reporte_service import (
    actualizar_vigencias_encharcamientos,
    buscar_duplicados_cercanos,
    cambiar_estado_reporte,
    crear_reporte,
    distancia_haversine_metros,
    serializar_reporte,
)

router = APIRouter(prefix="/reportes", tags=["Reportes Ciudadanos"])
TZ_JUAREZ = ZoneInfo(settings.TIMEZONE)


@router.get("", response_model=PaginatedReportesOut)
def listar_reportes(
    categoria: CategoriaReporte | None = None,
    estado: EstadoReporte | None = None,
    colonia_id: int | None = None,
    severidad: SeveridadBache | None = None,
    q: str | None = None,
    solo_activos: bool = True,
    pagina: int = Query(1, ge=1),
    tamano_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_current_user_optional),
):
    actualizar_vigencias_encharcamientos(db)
    query = db.query(Reporte).options(joinedload(Reporte.colonia), joinedload(Reporte.interacciones))

    # Visitantes y ciudadanos no ven reportes rechazados (RN-09, HU-04.1 CA4)
    if not current_user or current_user.rol == RolUsuario.CIUDADANO:
        query = query.filter(Reporte.estado != EstadoReporte.RECHAZADO)
        if solo_activos and not estado:
            query = query.filter(
                Reporte.estado.notin_([EstadoReporte.REPARADO, EstadoReporte.HISTORICO, EstadoReporte.RECHAZADO])
            )

    if categoria:
        query = query.filter(Reporte.categoria == categoria)
    if estado:
        query = query.filter(Reporte.estado == estado)
    if colonia_id:
        query = query.filter(Reporte.colonia_id == colonia_id)
    if severidad:
        query = query.filter(Reporte.severidad == severidad)
    if q:
        patron = f"%{q.strip()}%"
        query = query.filter(or_(Reporte.calle.ilike(patron), Reporte.folio.ilike(patron)))

    total = query.count()
    items_db = (
        query.order_by(Reporte.fecha_reporte.desc())
        .offset((pagina - 1) * tamano_pagina)
        .limit(tamano_pagina)
        .all()
    )
    items = [serializar_reporte(r) for r in items_db]
    return PaginatedReportesOut(total=total, pagina=pagina, tamano_pagina=tamano_pagina, items=items)


@router.get("/cerca", response_model=list[ReporteOut])
def consultar_mi_zona(
    lat: float,
    lon: float,
    radio_metros: float = Query(1000.0, ge=100, le=5000),
    db: Session = Depends(get_db),
):
    """HU-04.3: Reportes activos a 1 km o menos, ordenados por distancia, resaltando Intransitable al inicio."""
    actualizar_vigencias_encharcamientos(db)
    activos = (
        db.query(Reporte)
        .options(joinedload(Reporte.colonia), joinedload(Reporte.interacciones))
        .filter(
            Reporte.estado.notin_(
                [EstadoReporte.REPARADO, EstadoReporte.HISTORICO, EstadoReporte.RECHAZADO]
            )
        )
        .all()
    )
    cercanos = []
    for rep in activos:
        dist = distancia_haversine_metros(lat, lon, rep.latitud, rep.longitud)
        if dist <= radio_metros:
            cercanos.append(serializar_reporte(rep, distancia=dist))

    # Intransitable primero (HU-04.3 CA2), luego del más cercano al más lejano
    cercanos.sort(
        key=lambda r: (
            0 if (r.categoria == CategoriaReporte.ENCHARCAMIENTO and r.nivel_agua == NivelAgua.INTRANSITABLE) else 1,
            r.distancia_metros or 0,
        )
    )
    return cercanos


@router.get("/verificar-duplicados", response_model=list[ReporteOut])
def verificar_duplicados(
    categoria: CategoriaReporte,
    lat: float,
    lon: float,
    db: Session = Depends(get_db),
):
    """HU-02.3 y HU-03.1 CA4: Detecta reportes abiertos a <=30m (bache) o <=50m (encharcamiento)."""
    return buscar_duplicados_cercanos(db, categoria, lat, lon)


@router.get("/mis-reportes", response_model=PaginatedReportesOut)
def listar_mis_reportes(
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = (
        db.query(Reporte)
        .options(joinedload(Reporte.colonia), joinedload(Reporte.interacciones))
        .filter(Reporte.autor_id == current_user.id)
    )
    total = query.count()
    items_db = query.order_by(Reporte.fecha_reporte.desc()).offset((pagina - 1) * 10).limit(10).all()
    return PaginatedReportesOut(
        total=total,
        pagina=pagina,
        tamano_pagina=10,
        items=[serializar_reporte(r, incluir_motivo=True) for r in items_db],
    )


@router.post("", response_model=ReporteOut, status_code=status.HTTP_201_CREATED)
def registrar_reporte(
    data: ReporteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    rep = crear_reporte(db, data, current_user)
    return serializar_reporte(rep, incluir_motivo=True)


@router.get("/{folio}", response_model=ReporteOut)
def detalle_reporte(
    folio: str,
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_current_user_optional),
):
    actualizar_vigencias_encharcamientos(db)
    rep = (
        db.query(Reporte)
        .options(joinedload(Reporte.colonia), joinedload(Reporte.historial), joinedload(Reporte.interacciones))
        .filter(Reporte.folio == folio.upper())
        .first()
    )
    if not rep:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    es_staff = current_user and current_user.rol in {RolUsuario.MODERADOR, RolUsuario.COORDINADOR}
    es_autor = current_user and current_user.id == rep.autor_id
    if rep.estado == EstadoReporte.RECHAZADO and not (es_staff or es_autor):
        raise HTTPException(status_code=404, detail="Reporte no disponible.")
    return serializar_reporte(rep, incluir_motivo=bool(es_staff or es_autor))


@router.patch("/{folio}", response_model=ReporteOut)
def editar_mi_reporte(
    folio: str,
    data: ReporteUpdateCiudadano,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    rep = db.query(Reporte).filter(Reporte.folio == folio.upper()).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    if rep.autor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes editar el reporte de otra persona (HU-01.3).")
    if rep.estado != EstadoReporte.RECIBIDO:
        raise HTTPException(status_code=400, detail="Solo puedes editar reportes en estado Recibido (HU-02.5).")

    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(rep, campo, valor)
    db.commit()
    db.refresh(rep)
    return serializar_reporte(rep, incluir_motivo=True)


@router.delete("/{folio}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mi_reporte(
    folio: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    rep = db.query(Reporte).filter(Reporte.folio == folio.upper()).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    if rep.autor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes eliminar el reporte de otra persona.")
    if rep.estado != EstadoReporte.RECIBIDO:
        raise HTTPException(status_code=400, detail="Un reporte que ya salió de Recibido nunca se borra (RN-07).")
    db.delete(rep)
    db.commit()


@router.post("/{folio}/interaccion", response_model=ReporteOut)
def interactuar_reporte(
    folio: str,
    data: InteraccionIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-02.3 y HU-03.3: Confirmar bache o confirmar/desmentir encharcamiento."""
    actualizar_vigencias_encharcamientos(db)
    rep = db.query(Reporte).filter(Reporte.folio == folio.upper()).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    if rep.autor_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes confirmar ni desmentir tu propio reporte.")

    ya_interactuo = (
        db.query(InteraccionReporte)
        .filter(InteraccionReporte.reporte_id == rep.id, InteraccionReporte.usuario_id == current_user.id)
        .first()
    )
    if ya_interactuo:
        raise HTTPException(status_code=409, detail="Ya registraste tu respuesta sobre este reporte.")

    ahora = datetime.now(TZ_JUAREZ)
    db.add(
        InteraccionReporte(
            reporte_id=rep.id,
            usuario_id=current_user.id,
            tipo=data.tipo,
            creado_en=ahora,
        )
    )
    db.flush()

    if rep.categoria == CategoriaReporte.ENCHARCAMIENTO and rep.estado == EstadoReporte.ACTIVO:
        if data.tipo == TipoInteraccion.CONFIRMACION:
            rep.vigente_hasta = ahora + timedelta(hours=settings.VIGENCIA_ENCHARCAMIENTO_HORAS)
        elif data.tipo == TipoInteraccion.DESMENTIDO:
            total_desmentidos = (
                db.query(InteraccionReporte)
                .filter(
                    InteraccionReporte.reporte_id == rep.id,
                    InteraccionReporte.tipo == TipoInteraccion.DESMENTIDO,
                )
                .count()
            )
            if total_desmentidos >= settings.DESMENTIDOS_PARA_HISTORICO:
                rep.estado = EstadoReporte.HISTORICO

    db.commit()
    db.refresh(rep)
    return serializar_reporte(rep)


@router.patch("/{folio}/estado", response_model=ReporteOut)
def actualizar_estado(
    folio: str,
    data: CambioEstadoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(
        require_roles(RolUsuario.MODERADOR, RolUsuario.COORDINADOR, RolUsuario.ENLACE_MUNICIPAL)
    ),
):
    rep = db.query(Reporte).filter(Reporte.folio == folio.upper()).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    actualizado = cambiar_estado_reporte(db, rep, data, current_user)
    return serializar_reporte(actualizado, incluir_motivo=True)