import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import (
    CategoriaReporte,
    Colonia,
    EstadoReporte,
    HistorialEstado,
    InteraccionReporte,
    Reporte,
    RolUsuario,
    TipoInteraccion,
    Usuario,
)
from app.schemas.schemas import CambioEstadoIn, ReporteCreate, ReporteOut
from app.services.external_apis import esta_en_juarez

TZ_JUAREZ = ZoneInfo(settings.TIMEZONE)

TRANSICIONES_BACHE = {
    EstadoReporte.RECIBIDO: {EstadoReporte.VALIDADO, EstadoReporte.RECHAZADO},
    EstadoReporte.VALIDADO: {EstadoReporte.PROGRAMADO, EstadoReporte.EN_REPARACION},
    EstadoReporte.PROGRAMADO: {EstadoReporte.EN_REPARACION},
    EstadoReporte.EN_REPARACION: {EstadoReporte.REPARADO},
    EstadoReporte.REPARADO: set(),
    EstadoReporte.RECHAZADO: set(),
}


def distancia_haversine_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def actualizar_vigencias_encharcamientos(db: Session) -> None:
    ahora = datetime.now(TZ_JUAREZ)
    expirados = (
        db.query(Reporte)
        .filter(
            Reporte.categoria == CategoriaReporte.ENCHARCAMIENTO,
            Reporte.estado == EstadoReporte.ACTIVO,
            Reporte.vigente_hasta <= ahora,
        )
        .all()
    )
    for rep in expirados:
        rep.estado = EstadoReporte.HISTORICO
    if expirados:
        db.commit()


def serializar_reporte(rep: Reporte, incluir_motivo: bool = False, distancia: float | None = None) -> ReporteOut:
    ahora = datetime.now(TZ_JUAREZ)
    fecha_rep = rep.fecha_reporte if rep.fecha_reporte.tzinfo else rep.fecha_reporte.replace(tzinfo=TZ_JUAREZ)
    if rep.fecha_reparacion:
        fin = datetime.combine(rep.fecha_reparacion, datetime.min.time(), tzinfo=TZ_JUAREZ)
    else:
        fin = ahora
    longevidad = max(0, (fin - fecha_rep).days)

    confirmaciones = sum(1 for i in rep.interacciones if i.tipo == TipoInteraccion.CONFIRMACION)
    desmentidos = sum(1 for i in rep.interacciones if i.tipo == TipoInteraccion.DESMENTIDO)

    return ReporteOut(
        id=rep.id,
        folio=rep.folio,
        categoria=rep.categoria,
        estado=rep.estado,
        calle=rep.calle,
        referencia=rep.referencia,
        latitud=rep.latitud,
        longitud=rep.longitud,
        colonia_id=rep.colonia_id,
        colonia_nombre=rep.colonia.nombre if rep.colonia else None,
        tipo_dano=rep.tipo_dano,
        tamano_bache=rep.tamano_bache,
        profundidad_aprox=rep.profundidad_aprox,
        carril_afectado=rep.carril_afectado,
        severidad=rep.severidad,
        alcantarilla_senalizada=rep.alcantarilla_senalizada,
        nivel_agua=rep.nivel_agua,
        riesgo_vehiculos_personas=rep.riesgo_vehiculos_personas,
        vigente_hasta=rep.vigente_hasta,
        descripcion=rep.descripcion,
        fecha_reporte=fecha_rep,
        fecha_reparacion=rep.fecha_reparacion,
        motivo_rechazo=rep.motivo_rechazo if incluir_motivo else None,
        confirmaciones=confirmaciones,
        desmentidos=desmentidos,
        longevidad_dias=longevidad,
        distancia_metros=round(distancia, 1) if distancia is not None else None,
        historial=rep.historial,
    )


def buscar_duplicados_cercanos(db: Session, categoria: CategoriaReporte, lat: float, lon: float) -> list[ReporteOut]:
    actualizar_vigencias_encharcamientos(db)
    radio = (
        settings.RADIO_DUPLICADO_BACHE_M
        if categoria == CategoriaReporte.BACHE
        else settings.RADIO_DUPLICADO_ENCHARCAMIENTO_M
    )
    estados_abiertos = (
        [EstadoReporte.RECIBIDO, EstadoReporte.VALIDADO, EstadoReporte.PROGRAMADO, EstadoReporte.EN_REPARACION]
        if categoria == CategoriaReporte.BACHE
        else [EstadoReporte.ACTIVO]
    )
    candidatos = db.query(Reporte).filter(Reporte.categoria == categoria, Reporte.estado.in_(estados_abiertos)).all()
    cercanos = []
    for rep in candidatos:
        dist = distancia_haversine_metros(lat, lon, rep.latitud, rep.longitud)
        if dist <= radio:
            cercanos.append(serializar_reporte(rep, distancia=dist))
    return sorted(cercanos, key=lambda x: x.distancia_metros or 0)


def crear_reporte(db: Session, data: ReporteCreate, usuario: Usuario) -> Reporte:
    if not esta_en_juarez(data.latitud, data.longitud):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La ubicación está fuera del municipio de Juárez, Chihuahua (RN-01).",
        )

    colonia = db.query(Colonia).filter(Colonia.id == data.colonia_id, Colonia.activa.is_(True)).first()
    if not colonia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colonia no válida o inactiva.")

    ahora = datetime.now(TZ_JUAREZ)
    hace_una_hora = ahora - timedelta(hours=1)
    recientes = (
        db.query(Reporte)
        .filter(Reporte.autor_id == usuario.id, Reporte.fecha_reporte >= hace_una_hora)
        .count()
    )
    if recientes >= settings.MAX_REPORTES_POR_HORA:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Has alcanzado el límite de 10 reportes por hora (RN-08).",
        )

    prefijo = "BCH" if data.categoria == CategoriaReporte.BACHE else "ENC"
    total_cat = db.query(Reporte).filter(Reporte.categoria == data.categoria).count() + 1
    folio = f"{prefijo}-{ahora.year}-{total_cat:06d}"

    estado_inicial = (
        EstadoReporte.RECIBIDO if data.categoria == CategoriaReporte.BACHE else EstadoReporte.ACTIVO
    )
    vigente_hasta = (
        ahora + timedelta(hours=settings.VIGENCIA_ENCHARCAMIENTO_HORAS)
        if data.categoria == CategoriaReporte.ENCHARCAMIENTO
        else None
    )

    nuevo = Reporte(
        folio=folio,
        categoria=data.categoria,
        estado=estado_inicial,
        calle=data.calle,
        referencia=data.referencia,
        latitud=data.latitud,
        longitud=data.longitud,
        colonia_id=data.colonia_id,
        tipo_dano=data.tipo_dano,
        tamano_bache=data.tamano_bache,
        profundidad_aprox=data.profundidad_aprox,
        carril_afectado=data.carril_afectado,
        severidad=data.severidad,
        alcantarilla_senalizada=data.alcantarilla_senalizada,
        nivel_agua=data.nivel_agua,
        riesgo_vehiculos_personas=data.riesgo_vehiculos_personas,
        vigente_hasta=vigente_hasta,
        descripcion=data.descripcion,
        fecha_reporte=ahora,
        autor_id=usuario.id,
    )
    db.add(nuevo)
    db.flush()

    db.add(
        HistorialEstado(
            reporte_id=nuevo.id,
            estado_anterior=None,
            estado_nuevo=estado_inicial,
            comentario_publico="Reporte registrado en la plataforma.",
            usuario_id=usuario.id,
            fecha_cambio=ahora,
        )
    )
    db.commit()
    db.refresh(nuevo)
    return nuevo


def cambiar_estado_reporte(db: Session, rep: Reporte, data: CambioEstadoIn, usuario: Usuario) -> Reporte:
    ahora = datetime.now(TZ_JUAREZ)
    nuevo = data.estado_nuevo

    if rep.categoria == CategoriaReporte.BACHE:
        permitidos = TRANSICIONES_BACHE.get(rep.estado, set())
        if nuevo not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transición no permitida de '{rep.estado.value}' a '{nuevo.value}' (RN-05).",
            )
        if nuevo in {EstadoReporte.VALIDADO, EstadoReporte.RECHAZADO} and usuario.rol != RolUsuario.MODERADOR:
            raise HTTPException(status_code=403, detail="Solo un moderador puede validar o rechazar.")
        if nuevo == EstadoReporte.RECHAZADO and not data.motivo_rechazo:
            raise HTTPException(status_code=400, detail="Debes indicar el motivo de rechazo.")
        if nuevo == EstadoReporte.REPARADO:
            if not data.fecha_reparacion:
                raise HTTPException(status_code=400, detail="Debes indicar la fecha de reparación.")
            fecha_orig = rep.fecha_reporte.date()
            if data.fecha_reparacion > ahora.date() or data.fecha_reparacion < fecha_orig:
                raise HTTPException(
                    status_code=400,
                    detail="La fecha de reparación no puede ser futura ni anterior a la fecha del reporte.",
                )
            rep.fecha_reparacion = data.fecha_reparacion
        if nuevo == EstadoReporte.RECHAZADO:
            rep.motivo_rechazo = data.motivo_rechazo
    else:
        if nuevo != EstadoReporte.RECHAZADO or usuario.rol != RolUsuario.MODERADOR:
            raise HTTPException(status_code=403, detail="Solo un moderador puede rechazar un encharcamiento.")
        rep.motivo_rechazo = data.motivo_rechazo or "Rechazado por moderación"

    anterior = rep.estado
    rep.estado = nuevo
    db.add(
        HistorialEstado(
            reporte_id=rep.id,
            estado_anterior=anterior,
            estado_nuevo=nuevo,
            comentario_publico=data.comentario_publico or f"Estado actualizado a {nuevo.value}.",
            usuario_id=usuario.id,
            fecha_cambio=ahora,
        )
    )
    db.commit()
    db.refresh(rep)
    return rep