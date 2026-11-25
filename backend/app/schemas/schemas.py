import re
from datetime import date, datetime

from app.models import (
    CategoriaReporte,
    EstadoReporte,
    NivelAgua,
    RolUsuario,
    SeveridadBache,
    TipoDanoBache,
    TipoInteraccion,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# --- Usuarios y Auth ---
class UsuarioRegistro(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    correo: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    acepto_privacidad: bool

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe tener al menos 8 caracteres y combinar letras y números.")
        return v

    @field_validator("acepto_privacidad")
    @classmethod
    def validar_privacidad(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Debes aceptar el aviso de privacidad para registrarte.")
        return v


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    correo: EmailStr
    rol: RolUsuario
    activo: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class CambioRolIn(BaseModel):
    rol: RolUsuario


class CambioActivoIn(BaseModel):
    activo: bool


# --- Catálogos ---
class SectorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    descripcion: str | None = None


class ColoniaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    codigo_postal: str | None = Field(None, max_length=10)
    sector_id: int


class ColoniaUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=120)
    codigo_postal: str | None = Field(None, max_length=10)
    sector_id: int | None = None
    activa: bool | None = None


class ColoniaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    codigo_postal: str | None
    activa: bool
    sector_id: int
    sector: SectorOut | None = None


# --- Reportes (Entrada y Salida sin datos personales del autor RN-04) ---
class ReporteCreate(BaseModel):
    categoria: CategoriaReporte
    calle: str = Field(..., min_length=3, max_length=180)
    referencia: str | None = Field(None, max_length=200)
    latitud: float
    longitud: float
    colonia_id: int
    descripcion: str = Field(..., min_length=5, max_length=500)

    # Bache (HU-02.2)
    tipo_dano: TipoDanoBache | None = None
    tamano_bache: str | None = None
    profundidad_aprox: str | None = None
    carril_afectado: str | None = None
    severidad: SeveridadBache | None = None
    alcantarilla_senalizada: bool | None = None

    # Encharcamiento (HU-03.1)
    nivel_agua: NivelAgua | None = None
    riesgo_vehiculos_personas: bool | None = None

    @model_validator(mode="after")
    def validar_campos_dinamicos(self):
        if self.categoria == CategoriaReporte.BACHE:
            if not self.tipo_dano:
                raise ValueError("Debes indicar el tipo de daño para reportes de bache.")
            if self.tipo_dano == TipoDanoBache.BACHE:
                if not self.tamano_bache or not self.profundidad_aprox or not self.carril_afectado:
                    raise ValueError("Para bache debes indicar tamaño, profundidad aproximada y carril afectado.")
            if self.tipo_dano == TipoDanoBache.ALCANTARILLA_SIN_TAPA:
                self.severidad = SeveridadBache.ALTA
                if self.alcantarilla_senalizada is None:
                    raise ValueError("Debes indicar si la alcantarilla sin tapa está señalizada.")
            elif not self.severidad:
                self.severidad = SeveridadBache.MEDIA

        elif self.categoria == CategoriaReporte.ENCHARCAMIENTO:
            if not self.nivel_agua:
                raise ValueError("Debes indicar el nivel del agua para encharcamientos.")
            if self.nivel_agua == NivelAgua.INTRANSITABLE and self.riesgo_vehiculos_personas is None:
                raise ValueError("Para nivel intransitable debes indicar si hay vehículos varados o personas en riesgo.")
        return self


class ReporteUpdateCiudadano(BaseModel):
    calle: str | None = Field(None, min_length=3, max_length=180)
    referencia: str | None = Field(None, max_length=200)
    descripcion: str | None = Field(None, min_length=5, max_length=500)
    severidad: SeveridadBache | None = None
    nivel_agua: NivelAgua | None = None


class CambioEstadoIn(BaseModel):
    estado_nuevo: EstadoReporte
    comentario_publico: str | None = Field(None, max_length=500)
    motivo_rechazo: str | None = Field(None, max_length=255)
    fecha_reparacion: date | None = None


class InteraccionIn(BaseModel):
    tipo: TipoInteraccion


class HistorialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estado_anterior: EstadoReporte | None
    estado_nuevo: EstadoReporte
    comentario_publico: str | None
    fecha_cambio: datetime


class ReporteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    folio: str
    categoria: CategoriaReporte
    estado: EstadoReporte
    calle: str
    referencia: str | None
    latitud: float
    longitud: float
    colonia_id: int
    colonia_nombre: str | None = None
    tipo_dano: TipoDanoBache | None
    tamano_bache: str | None
    profundidad_aprox: str | None
    carril_afectado: str | None
    severidad: SeveridadBache | None
    alcantarilla_senalizada: bool | None
    nivel_agua: NivelAgua | None
    riesgo_vehiculos_personas: bool | None
    vigente_hasta: datetime | None
    descripcion: str
    fecha_reporte: datetime
    fecha_reparacion: date | None
    motivo_rechazo: str | None = None
    confirmaciones: int = 0
    desmentidos: int = 0
    longevidad_dias: int = 0
    distancia_metros: float | None = None
    historial: list[HistorialOut] = []


class PaginatedReportesOut(BaseModel):
    total: int
    pagina: int
    tamano_pagina: int
    items: list[ReporteOut]