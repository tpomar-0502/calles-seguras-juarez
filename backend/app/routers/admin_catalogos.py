import csv
import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import (
    CategoriaReporte,
    Colonia,
    EstadoReporte,
    Reporte,
    RolUsuario,
    Sector,
    Usuario,
)
from app.schemas.schemas import (
    CambioActivoIn,
    CambioRolIn,
    ColoniaCreate,
    ColoniaOut,
    ColoniaUpdate,
    SectorOut,
    UsuarioOut,
)
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

router = APIRouter(tags=["Catálogos, Tablero y Administración"])
TZ_JUAREZ = ZoneInfo(settings.TIMEZONE)


@router.get("/catalogos/sectores", response_model=list[SectorOut])
def listar_sectores(db: Session = Depends(get_db)):
    return db.query(Sector).order_by(Sector.nombre).all()


@router.get("/catalogos/colonias", response_model=list[ColoniaOut])
def listar_colonias(incluir_inactivas: bool = False, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Colonia).options(joinedload(Colonia.sector))
    if not incluir_inactivas:
        query = query.filter(Colonia.activa.is_(True))
    if q:
        query = query.filter(Colonia.nombre.ilike(f"%{q.strip()}%"))
    return query.order_by(Colonia.nombre).all()


@router.post("/catalogos/colonias", response_model=ColoniaOut, status_code=status.HTTP_201_CREATED)
def crear_colonia(
    data: ColoniaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.COORDINADOR)),
):
    duplicada = (
        db.query(Colonia)
        .filter(func.lower(Colonia.nombre) == data.nombre.strip().lower(), Colonia.sector_id == data.sector_id)
        .first()
    )
    if duplicada:
        raise HTTPException(status_code=409, detail="Ya existe una colonia con ese nombre en el mismo sector.")
    col = Colonia(nombre=data.nombre.strip(), codigo_postal=data.codigo_postal, sector_id=data.sector_id, activa=True)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.patch("/catalogos/colonias/{colonia_id}", response_model=ColoniaOut)
def editar_colonia(
    colonia_id: int,
    data: ColoniaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.COORDINADOR)),
):
    col = db.query(Colonia).filter(Colonia.id == colonia_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Colonia no encontrada.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(col, campo, valor)
    db.commit()
    db.refresh(col)
    return col


@router.get("/admin/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    q: str | None = None,
    rol: RolUsuario | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.COORDINADOR)),
):
    query = db.query(Usuario)
    if q:
        p = f"%{q.strip()}%"
        query = query.filter((Usuario.nombre.ilike(p)) | (Usuario.correo.ilike(p)))
    if rol:
        query = query.filter(Usuario.rol == rol)
    return query.order_by(Usuario.id).all()


@router.patch("/admin/usuarios/{usuario_id}/rol", response_model=UsuarioOut)
def cambiar_rol_usuario(
    usuario_id: int,
    data: CambioRolIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(RolUsuario.COORDINADOR)),
):
    objetivo = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not objetivo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if objetivo.id == current_user.id and data.rol != RolUsuario.COORDINADOR:
        total_coords = (
            db.query(Usuario).filter(Usuario.rol == RolUsuario.COORDINADOR, Usuario.activo.is_(True)).count()
        )
        if total_coords <= 1:
            raise HTTPException(status_code=400, detail="No puedes quitar el rol al único coordinador activo.")
    objetivo.rol = data.rol
    db.commit()
    db.refresh(objetivo)
    return objetivo


@router.patch("/admin/usuarios/{usuario_id}/activo", response_model=UsuarioOut)
def suspender_activar_usuario(
    usuario_id: int,
    data: CambioActivoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(RolUsuario.COORDINADOR)),
):
    objetivo = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not objetivo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if objetivo.id == current_user.id and not data.activo:
        raise HTTPException(status_code=400, detail="No puedes suspender tu propia cuenta de coordinador.")
    objetivo.activo = data.activo
    db.commit()
    db.refresh(objetivo)
    return objetivo


@router.get("/admin/tablero")
def obtener_indicadores_tablero(
    sector_id: int | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.COORDINADOR, RolUsuario.MODERADOR)),
):
    """HU-07.1: Indicadores principales para la mesa directiva."""
    query = db.query(Reporte).options(joinedload(Reporte.colonia))
    if sector_id:
        query = query.join(Colonia).filter(Colonia.sector_id == sector_id)
    reportes = query.all()
    ahora = datetime.now(TZ_JUAREZ)

    por_categoria = {"bache": 0, "encharcamiento": 0}
    por_estado: dict[str, int] = {}
    baches_abiertos_por_colonia: dict[str, list[int]] = {}
    tiempos_reparacion: list[int] = []
    baches_longevidad = []

    for r in reportes:
        por_categoria[r.categoria.value] = por_categoria.get(r.categoria.value, 0) + 1
        por_estado[r.estado.value] = por_estado.get(r.estado.value, 0) + 1
        f_rep = r.fecha_reporte if r.fecha_reporte.tzinfo else r.fecha_reporte.replace(tzinfo=TZ_JUAREZ)

        if r.categoria == CategoriaReporte.BACHE:
            if r.estado not in {EstadoReporte.REPARADO, EstadoReporte.RECHAZADO}:
                dias = max(0, (ahora - f_rep).days)
                col_nombre = r.colonia.nombre if r.colonia else "Sin colonia"
                baches_abiertos_por_colonia.setdefault(col_nombre, []).append(dias)
                baches_longevidad.append(
                    {"folio": r.folio, "calle": r.calle, "colonia": col_nombre, "dias": dias, "estado": r.estado.value}
                )
            elif r.estado == EstadoReporte.REPARADO and r.fecha_reparacion:
                fin = datetime.combine(r.fecha_reparacion, datetime.min.time(), tzinfo=TZ_JUAREZ)
                tiempos_reparacion.append(max(0, (fin - f_rep).days))

    top_colonias = sorted(
        [
            {
                "colonia": col,
                "baches_abiertos": len(dias_lista),
                "longevidad_promedio_dias": round(sum(dias_lista) / len(dias_lista), 1),
            }
            for col, dias_lista in baches_abiertos_por_colonia.items()
        ],
        key=lambda x: x["baches_abiertos"],
        reverse=True,
    )[:10]

    top_longevidad = sorted(baches_longevidad, key=lambda x: x["dias"], reverse=True)[:10]

    # Serie semanal (últimas 12 semanas)
    semanas = []
    for w in range(11, -1, -1):
        inicio_sem = ahora - timedelta(days=(w + 1) * 7)
        fin_sem = ahora - timedelta(days=w * 7)
        conteo = sum(
            1
            for r in reportes
            if inicio_sem
            <= (r.fecha_reporte if r.fecha_reporte.tzinfo else r.fecha_reporte.replace(tzinfo=TZ_JUAREZ))
            < fin_sem
        )
        semanas.append({"semana": f"Sem -{w}" if w > 0 else "Actual", "total": conteo})

    promedio_rep = round(sum(tiempos_reparacion) / len(tiempos_reparacion), 1) if tiempos_reparacion else 0.0

    return {
        "total_reportes": len(reportes),
        "por_categoria": por_categoria,
        "por_estado": por_estado,
        "tiempo_promedio_reparacion_dias": promedio_rep,
        "top_10_colonias": top_colonias,
        "top_10_longevidad": top_longevidad,
        "tendencia_12_semanas": semanas,
    }


@router.get("/admin/exportar")
def exportar_reportes_autoridad(
    formato: str = "csv",
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles(RolUsuario.COORDINADOR)),
):
    """HU-07.3 + Punto Extra: Exportación anónima en CSV o XML para la autoridad municipal."""
    reportes = (
        db.query(Reporte)
        .options(joinedload(Reporte.colonia))
        .filter(Reporte.estado != EstadoReporte.RECHAZADO)
        .order_by(Reporte.fecha_reporte.desc())
        .all()
    )

    if formato.lower() == "xml":
        root = ET.Element("reportes_calles_seguras_juarez", generado_en=datetime.now(TZ_JUAREZ).isoformat())
        for r in reportes:
            nodo = ET.SubElement(root, "reporte", folio=r.folio, categoria=r.categoria.value)
            ET.SubElement(nodo, "estado").text = r.estado.value
            ET.SubElement(nodo, "calle").text = r.calle
            ET.SubElement(nodo, "colonia").text = r.colonia.nombre if r.colonia else ""
            ET.SubElement(nodo, "latitud").text = str(r.latitud)
            ET.SubElement(nodo, "longitud").text = str(r.longitud)
            ET.SubElement(nodo, "fecha_reporte").text = r.fecha_reporte.isoformat()
        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return Response(
            content=xml_bytes,
            media_type="application/xml",
            headers={"Content-Disposition": "attachment; filename=reportes_juarez.xml"},
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Folio", "Categoria", "Estado", "Calle", "Colonia", "Latitud", "Longitud", "FechaReporte"])
    for r in reportes:
        writer.writerow(
            [
                r.folio,
                r.categoria.value,
                r.estado.value,
                r.calle,
                r.colonia.nombre if r.colonia else "",
                r.latitud,
                r.longitud,
                r.fecha_reporte.isoformat(),
            ]
        )
    return Response(
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reportes_juarez.csv"},
    )