import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api/client";
import { PaginatedReportes, Reporte } from "../types";

export const MyReportsPage: React.FC = () => {
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = () => {
    setCargando(true);
    apiFetch<PaginatedReportes>("/reportes/mis-reportes")
      .then((res) => setReportes(res.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargar();
  }, []);

  const eliminar = async (folio: string) => {
    if (!confirm(`¿Seguro que deseas eliminar el reporte ${folio}?`)) return;
    try {
      await apiFetch(`/reportes/${folio}`, { method: "DELETE" });
      cargar();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const editarDescripcion = async (rep: Reporte) => {
    const nueva = prompt("Nueva descripción del reporte:", rep.descripcion);
    if (!nueva || nueva.trim() === rep.descripcion) return;
    try {
      await apiFetch(`/reportes/${rep.folio}`, {
        method: "PATCH",
        body: JSON.stringify({ descripcion: nueva.trim() }),
      });
      cargar();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  return (
    <div className="container page-content">
      <div className="section-header">
        <h1>Mis reportes</h1>
        <Link to="/reportar" className="btn btn-primary">+ Nuevo reporte</Link>
      </div>

      {cargando && <p>Cargando tus reportes...</p>}
      {error && <p className="error-box" role="alert">{error}</p>}

      {!cargando && reportes.length === 0 && (
        <div className="empty-box">
          <p>Aún no has registrado ningún reporte en la plataforma.</p>
          <Link to="/reportar" className="btn btn-primary btn-sm">Crear mi primer reporte</Link>
        </div>
      )}

      {reportes.length > 0 && (
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Folio</th>
                <th>Tipo</th>
                <th>Calle y Colonia</th>
                <th>Fecha</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {reportes.map((r) => (
                <tr key={r.id}>
                  <td><Link to={`/reportes/${r.folio}`}>{r.folio}</Link></td>
                  <td>{r.categoria}</td>
                  <td>{r.calle} ({r.colonia_nombre})</td>
                  <td>{new Date(r.fecha_reporte).toLocaleDateString("es-MX")}</td>
                  <td>
                    {r.estado}
                    {r.motivo_rechazo && <small className="block-note">Motivo: {r.motivo_rechazo}</small>}
                  </td>
                  <td>
                    {r.estado === "Recibido" ? (
                      <div className="btn-group">
                        <button type="button" className="btn btn-secondary btn-sm" onClick={() => editarDescripcion(r)}>
                          Editar
                        </button>
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => eliminar(r.folio)}>
                          Eliminar
                        </button>
                      </div>
                    ) : (
                      <span className="muted-text">En seguimiento</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};