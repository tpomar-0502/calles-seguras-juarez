export type RolUsuario = "ciudadano" | "moderador" | "coordinador" | "enlace_municipal";
export type CategoriaReporte = "bache" | "encharcamiento";
export type TipoDanoBache = "bache" | "hundimiento" | "grieta" | "alcantarilla_sin_tapa";
export type SeveridadBache = "Baja" | "Media" | "Alta";
export type NivelAgua = "a un lado de la calle" | "cubre un carril" | "a media llanta" | "intransitable";

export interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  rol: RolUsuario;
  activo: boolean;
}

export interface Colonia {
  id: number;
  nombre: string;
  codigo_postal: string | null;
  activa: boolean;
  sector_id: number;
  sector?: { id: number; nombre: string };
}

export interface HistorialItem {
  id: number;
  estado_anterior: string | null;
  estado_nuevo: string;
  comentario_publico: string | null;
  fecha_cambio: string;
}

export interface Reporte {
  id: number;
  folio: string;
  categoria: CategoriaReporte;
  estado: string;
  calle: string;
  referencia: string | null;
  latitud: number;
  longitud: number;
  colonia_id: number;
  colonia_nombre: string | null;
  tipo_dano: TipoDanoBache | null;
  tamano_bache: string | null;
  profundidad_aprox: string | null;
  carril_afectado: string | null;
  severidad: SeveridadBache | null;
  alcantarilla_senalizada: boolean | null;
  nivel_agua: NivelAgua | null;
  riesgo_vehiculos_personas: boolean | null;
  vigente_hasta: string | null;
  descripcion: string;
  fecha_reporte: string;
  fecha_reparacion: string | null;
  motivo_rechazo: string | null;
  confirmaciones: number;
  desmentidos: number;
  longevidad_dias: number;
  distancia_metros: number | null;
  historial: HistorialItem[];
}

export interface PaginatedReportes {
  total: number;
  pagina: number;
  tamano_pagina: number;
  items: Reporte[];
}

export interface ClimaJuarez {
  disponible: boolean;
  hay_lluvia: boolean;
  probabilidad_maxima: number | null;
  mensaje: string;
}