import enum
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

TZ_JUAREZ = ZoneInfo("America/Ciudad_Juarez")


def now_juarez() -> datetime:
    return datetime.now(TZ_JUAREZ)


class RolUsuario(str, enum.Enum):
    CIUDADANO = "ciudadano"
    MODERADOR = "moderador"
    COORDINADOR = "coordinador"
    ENLACE_MUNICIPAL = "enlace_municipal"


class CategoriaReporte(str, enum.Enum):
    BACHE = "bache"
    ENCHARCAMIENTO = "encharcamiento"


class TipoDanoBache(str, enum.Enum):
    BACHE = "bache"
    HUNDIMIENTO = "hundimiento"
    GRIETA = "grieta"
    ALCANTARILLA_SIN_TAPA = "alcantarilla_sin_tapa"


class SeveridadBache(str, enum.Enum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


class NivelAgua(str, enum.Enum):
    LADO_CALLE = "a un lado de la calle"
    UN_CARRIL = "cubre un carril"
    MEDIA_LLANTA = "a media llanta"
    INTRANSITABLE = "intransitable"


class EstadoReporte(str, enum.Enum):
    # Ciclo de Bache (RN-05)
    RECIBIDO = "Recibido"
    VALIDADO = "Validado"
    PROGRAMADO = "Programado"
    EN_REPARACION = "En reparación"
    REPARADO = "Reparado"
    RECHAZADO = "Rechazado"
    # Ciclo de Encharcamiento (RN-06)
    ACTIVO = "Activo"
    HISTORICO = "Histórico"


class TipoInteraccion(str, enum.Enum):
    CONFIRMACION = "confirmacion"
    DESMENTIDO = "desmentido"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(Enum(RolUsuario), default=RolUsuario.CIUDADANO, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    acepto_privacidad = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime(timezone=True), default=now_juarez, nullable=False)

    # Relaciones 1:N y N:M
    reportes = relationship("Reporte", back_populates="autor")
    interacciones = relationship("InteraccionReporte", back_populates="usuario")
    colonias_interes = relationship(
        "Colonia", secondary="usuario_colonias_interes", back_populates="usuarios_interesados"
    )


class Sector(Base):
    __tablename__ = "sectores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    colonias = relationship("Colonia", back_populates="sector", cascade="all, delete-orphan")


class Colonia(Base):
    __tablename__ = "colonias"
    __table_args__ = (UniqueConstraint("nombre", "sector_id", name="uq_colonia_sector"),)

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), index=True, nullable=False)
    codigo_postal = Column(String(10), nullable=True)
    activa = Column(Boolean, default=True, nullable=False)
    sector_id = Column(Integer, ForeignKey("sectores.id"), nullable=False)

    sector = relationship("Sector", back_populates="colonias")
    reportes = relationship("Reporte", back_populates="colonia")
    usuarios_interesados = relationship(
        "Usuario", secondary="usuario_colonias_interes", back_populates="colonias_interes"
    )


# Tabla asociativa N:M explícita: Usuarios <-> Colonias de interés (HU-01.4)
class UsuarioColoniaInteres(Base):
    __tablename__ = "usuario_colonias_interes"

    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    colonia_id = Column(Integer, ForeignKey("colonias.id", ondelete="CASCADE"), primary_key=True)


class Reporte(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String(25), unique=True, index=True, nullable=False)  # BCH-2026-000001 / ENC-2026-000001
    categoria = Column(Enum(CategoriaReporte), index=True, nullable=False)
    estado = Column(Enum(EstadoReporte), index=True, nullable=False)

    # Ubicación (RN-01)
    calle = Column(String(180), index=True, nullable=False)
    referencia = Column(String(200), nullable=True)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    colonia_id = Column(Integer, ForeignKey("colonias.id"), nullable=False)

    # Campos específicos de Bache (HU-02.2)
    tipo_dano = Column(Enum(TipoDanoBache), nullable=True)
    tamano_bache = Column(String(40), nullable=True)  # chico, mediano, grande
    profundidad_aprox = Column(String(40), nullable=True)
    carril_afectado = Column(String(60), nullable=True)
    severidad = Column(Enum(SeveridadBache), nullable=True)
    alcantarilla_senalizada = Column(Boolean, nullable=True)

    # Campos específicos de Encharcamiento (HU-03.1, HU-03.2)
    nivel_agua = Column(Enum(NivelAgua), nullable=True)
    riesgo_vehiculos_personas = Column(Boolean, nullable=True)
    vigente_hasta = Column(DateTime(timezone=True), nullable=True)

    # Generales y trazabilidad (RN-07, RN-10)
    descripcion = Column(String(500), nullable=False)
    fecha_reporte = Column(DateTime(timezone=True), default=now_juarez, nullable=False)
    fecha_reparacion = Column(Date, nullable=True)
    motivo_rechazo = Column(String(255), nullable=True)
    folio_principal_id = Column(Integer, ForeignKey("reportes.id"), nullable=True)

    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    autor = relationship("Usuario", back_populates="reportes")
    colonia = relationship("Colonia", back_populates="reportes")
    historial = relationship(
        "HistorialEstado", back_populates="reporte", order_by="desc(HistorialEstado.fecha_cambio)"
    )
    interacciones = relationship("InteraccionReporte", back_populates="reporte")


class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id = Column(Integer, primary_key=True, index=True)
    reporte_id = Column(Integer, ForeignKey("reportes.id", ondelete="CASCADE"), nullable=False)
    estado_anterior = Column(Enum(EstadoReporte), nullable=True)
    estado_nuevo = Column(Enum(EstadoReporte), nullable=False)
    comentario_publico = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_cambio = Column(DateTime(timezone=True), default=now_juarez, nullable=False)

    reporte = relationship("Reporte", back_populates="historial")
    usuario = relationship("Usuario")


# Tabla asociativa N:M con atributos: Usuarios <-> Reportes (Confirmaciones / Desmentidos)
class InteraccionReporte(Base):
    __tablename__ = "interacciones_reporte"

    id = Column(Integer, primary_key=True, index=True)
    reporte_id = Column(Integer, ForeignKey("reportes.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(Enum(TipoInteraccion), nullable=False)
    ciclo_vigencia = Column(Integer, default=1, nullable=False)
    creado_en = Column(DateTime(timezone=True), default=now_juarez, nullable=False)

    reporte = relationship("Reporte", back_populates="interacciones")
    usuario = relationship("Usuario", back_populates="interacciones")