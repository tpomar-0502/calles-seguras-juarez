import React from "react";
import { Link } from "react-router-dom";
import { Reporte } from "../types";

interface Props {
  reporte: Reporte;
}

export const ReportCard: React.FC<Props> = ({ reporte }) => {
  const esIntransitable =
    reporte.categoria === "encharcamiento" && reporte.nivel_agua === "intransitable";

  return (
    <article className={`report-card ${esIntransitable ? "card-critical" : ""}`}>
      <div className="card-top">
        <span className={`tag tag-${reporte.categoria}`}>
          {reporte.categoria === "bache" ? "Bache / Pavimento" : "Encharcamiento"}
        </span>
        <span className="folio-code">{reporte.folio}</span>
      </div>

      <h3 className="card-title">{reporte.calle}</h3>
      <p className="card-meta">
        Colonia: <strong>{reporte.colonia_nombre || "Ciudad Juárez"}</strong>
        {reporte.distancia_metros !== null && (
          <span className="distance-chip"> · A {reporte.distancia_metros} m</span>
        )}
      </p>

      <p className="card-desc">{reporte.descripcion}</p>

      <div className="card-badges">
        <span className="badge-info">
          Estado: <strong>{reporte.estado === "Recibido" ? "Sin validar" : reporte.estado}</strong>
        </span>
        {reporte.categoria === "bache" && reporte.severidad && (
          <span className={`badge-sev sev-${reporte.severidad.toLowerCase()}`}>
            Severidad: {reporte.severidad}
          </span>
        )}
        {reporte.categoria === "encharcamiento" && reporte.nivel_agua && (
          <span className={`badge-sev ${esIntransitable ? "sev-alta" : "sev-media"}`}>
            Nivel: {reporte.nivel_agua}
          </span>
        )}
        <span className="badge-neutral">Reportado hace: {reporte.longevidad_dias} d</span>
        <span className="badge-neutral">Confirmaciones: {reporte.confirmaciones}</span>
      </div>

      <div className="card-actions">
        <Link to={`/reportes/${reporte.folio}`} className="btn btn-secondary btn-sm">
          Ver detalle e historial
        </Link>
      </div>
    </article>
  );
};