import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { PaginatedReportes, Reporte } from "../types";

export const ModerationPage: React.FC = () => {
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [filtroEstado, setFiltroEstado] = useState("Recibido");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = () => {
    setCargando(true);
    const query = filtroEstado ? `?estado=${encodeURIComponent(filtroEstado)}&solo_activos=false&tamano_pagina=50` : "?solo_activos=false&tamano_pagina=50";
    apiFetch<PaginatedReportes>(`/reportes${query}`)
      .then((res) => setReportes(res.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
  }, [filtroEstado]);

  const cambiarEstado = async (rep: Reporte, estadoNuevo: string) => {
    let motivoRechazo: string | undefined;
    let fechaReparacion: string | undefined;

    if (estadoNuevo === "Rechazado") {
      const m = prompt("Motivo de rechazo (duplicado, fuera del municipio, no es vía pública, inapropiado):");
      if (!m) return;
      motivoRechazo = m;
    }

    if (estadoNuevo === "Reparado") {
      const hoy = new Date().toISOString().split("T")[0];
      const f = prompt("Fecha de reparación (YYYY-MM-DD):", hoy);
      if (!f) return;
      fechaReparacion = f;
    }

    const comentario = prompt("Comentario público de seguimiento (opcional):") || undefined;

    try {
      await apiFetch(`/reportes/${rep.folio}/estado`, {
        method: "PATCH",
        body: JSON.stringify({
          estado_nuevo: estadoNuevo,
          comentario_publico: comentario,
          motivo_rechazo: motivoRechazo,
          fecha_reparacion: fechaReparacion,
        }),
      });
      cargar();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  return (
    <div className="container page-content">
      <h1>Bandeja de Moderación y Seguimiento</h1>

      <div className="form-group max-w-sm">
        <label htmlFor="mod-estado">Filtrar por estado</label>
        <select id="mod-estado" value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
          <option value="Recibido">Recibido (Por validar)</option>
          <option value="Validado">Validado</option>
          <option value="Programado">Programado</option>
          <option value="En reparación">En reparación</option>
          <option value="Reparado">Reparado</option>
          <option value="Rechazado">Rechazado</option>
        </select>
      </div>

      {cargando && <p>Cargando bandeja...</p>}
      {error && <p className="error-box" role="alert">{error}</p>}

      <div className="table-responsive mt-1">
        <table className="data-table">
          <thead>
            <tr>
              <th>Folio</th>
              <th>Categoría</th>
              <th>Ubicación</th>
              <th>Detalle</th>
              <th>Estado</th>
              <th>Acciones permitidas</th>
            </tr>
          </thead>
          <tbody>
            {reportes.map((r) => (
              <tr key={r.id}>
                <td><strong>{r.folio}</strong></td>
                <td>{r.categoria}</td>
                <td>{r.calle} — {r.colonia_nombre}</td>
                <td>{r.descripcion}</td>
                <td>{r.estado}</td>
                <td>
                  <div className="btn-group">
                    {r.estado === "Recibido" && (
                      <>
                        <button type="button" className="btn btn-primary btn-sm" onClick={() => cambiarEstado(r, "Validado")}>
                          Validar
                        </button>
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => cambiarEstado(r, "Rechazado")}>
                          Rechazar
                        </button>
                      </>
                    )}
                    {r.estado === "Validado" && (
                      <>
                        <button type="button" className="btn btn-secondary btn-sm" onClick={() => cambiarEstado(r, "Programado")}>
                          Programar
                        </button>
                        <button type="button" className="btn btn-primary btn-sm" onClick={() => cambiarEstado(r, "En reparación")}>
                          En reparación
                        </button>
                      </>
                    )}
                    {r.estado === "Programado" && (
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => cambiarEstado(r, "En reparación")}>
                        Iniciar reparación
                      </button>
                    )}
                    {r.estado === "En reparación" && (
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => cambiarEstado(r, "Reparado")}>
                        Marcar Reparado
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};