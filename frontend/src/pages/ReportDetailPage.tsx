import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch } from "../api/client";
import { useAuth } from "../api/AuthContext";
import { Reporte } from "../types";

export const ReportDetailPage: React.FC = () => {
  const { folio } = useParams<{ folio: string }>();
  const { usuario } = useAuth();
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mensajeAccion, setMensajeAccion] = useState<string | null>(null);

  const cargar = () => {
    if (!folio) return;
    setCargando(true);
    apiFetch<Reporte>(`/reportes/${folio}`)
      .then(setReporte)
      .catch((err: Error) => setError(err.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
  }, [folio]);

  const enviarInteraccion = async (tipo: "confirmacion" | "desmentido") => {
    if (!folio) return;
    setMensajeAccion(null);
    try {
      const actualizado = await apiFetch<Reporte>(`/reportes/${folio}/interaccion`, {
        method: "POST",
        body: JSON.stringify({ tipo }),
      });
      setReporte(actualizado);
      setMensajeAccion(
        tipo === "confirmacion"
          ? "Tu confirmación fue registrada."
          : "Tu aviso de que ya no hay agua fue registrado."
      );
    } catch (err) {
      setMensajeAccion((err as Error).message);
    }
  };

  if (cargando) return <div className="container page-content"><p>Cargando detalle...</p></div>;
  if (error || !reporte) {
    return (
      <div className="container page-content">
        <p className="error-box" role="alert">{error || "Reporte no encontrado."}</p>
        <Link to="/" className="btn btn-secondary">Volver a explorar</Link>
      </div>
    );
  }

  return (
    <div className="container page-content">
      <Link to="/" className="back-link">&larr; Volver al listado</Link>

      <article className="panel-box">
        <div className="card-top">
          <span className={`tag tag-${reporte.categoria}`}>{reporte.categoria.toUpperCase()}</span>
          <span className="folio-code">{reporte.folio}</span>
        </div>

        <h1>{reporte.calle}</h1>
        <p><strong>Colonia:</strong> {reporte.colonia_nombre} · <strong>Estado actual:</strong> {reporte.estado}</p>
        <p><strong>Descripción:</strong> {reporte.descripcion}</p>

        <dl className="detail-grid">
          <div>
            <dt>Fecha de reporte (Hora Juárez)</dt>
            <dd>{new Date(reporte.fecha_reporte).toLocaleString("es-MX")}</dd>
          </div>
          <div>
            <dt>Longevidad</dt>
            <dd>{reporte.longevidad_dias} días</dd>
          </div>
          <div>
            <dt>Confirmaciones ciudadanas</dt>
            <dd>{reporte.confirmaciones}</dd>
          </div>
          {reporte.categoria === "bache" ? (
            <>
              <div><dt>Tipo de daño</dt><dd>{reporte.tipo_dano}</dd></div>
              <div><dt>Severidad</dt><dd>{reporte.severidad}</dd></div>
              {reporte.tamano_bache && <div><dt>Tamaño / Profundidad</dt><dd>{reporte.tamano_bache} ({reporte.profundidad_aprox})</dd></div>}
            </>
          ) : (
            <>
              <div><dt>Nivel de agua</dt><dd>{reporte.nivel_agua}</dd></div>
              <div><dt>Desmentidos ("Ya bajó el agua")</dt><dd>{reporte.desmentidos} / 3</dd></div>
            </>
          )}
        </dl>

        {usuario && (
          <div className="interaction-bar">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => enviarInteraccion("confirmacion")}
            >
              Sigue ahí (Confirmar reporte)
            </button>
            {reporte.categoria === "encharcamiento" && reporte.estado === "Activo" && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => enviarInteraccion("desmentido")}
              >
                Ya no hay agua (Desmentir)
              </button>
            )}
          </div>
        )}
        {mensajeAccion && <p className="status-note">{mensajeAccion}</p>}
      </article>

      <section className="panel-box" aria-labelledby="titulo-historial">
        <h2 id="titulo-historial">Historial de seguimiento</h2>
        <ul className="timeline-list">
          {reporte.historial.map((h) => (
            <li key={h.id} className="timeline-item">
              <strong>{h.estado_nuevo}</strong> —{" "}
              <time>{new Date(h.fecha_cambio).toLocaleString("es-MX")}</time>
              {h.comentario_publico && <p>{h.comentario_publico}</p>}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};