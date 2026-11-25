import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { Colonia, RolUsuario, Usuario } from "../types";

interface TableroData {
  total_reportes: number;
  por_categoria: { bache: number; encharcamiento: number };
  por_estado: Record<string, number>;
  tiempo_promedio_reparacion_dias: number;
  top_10_colonias: { colonia: string; baches_abiertos: number; longevidad_promedio_dias: number }[];
  top_10_longevidad: { folio: string; calle: string; colonia: string; dias: number; estado: string }[];
  tendencia_12_semanas: { semana: string; total: number }[];
}

export const AdminDashboardPage: React.FC = () => {
  const [tablero, setTablero] = useState<TableroData | null>(null);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [colonias, setColonias] = useState<Colonia[]>([]);
  const [sectores, setSectores] = useState<{ id: number; nombre: string }[]>([]);
  const [sectorFiltro, setSectorFiltro] = useState("");

  // Alta colonia HU-06.1
  const [nuevaColonia, setNuevaColonia] = useState("");
  const [nuevoCp, setNuevoCp] = useState("");
  const [sectorColonia, setSectorColonia] = useState<number>(1);

  const cargarTodo = () => {
    const query = sectorFiltro ? `?sector_id=${sectorFiltro}` : "";
    apiFetch<TableroData>(`/admin/tablero${query}`).then(setTablero).catch(() => {});
    apiFetch<Usuario[]>("/admin/usuarios").then(setUsuarios).catch(() => {});
    apiFetch<Colonia[]>("/catalogos/colonias?incluir_inactivas=true").then(setColonias).catch(() => {});
    apiFetch<{ id: number; nombre: string }[]>("/catalogos/sectores").then((s) => {
      setSectores(s);
      if (s.length > 0 && !sectorColonia) setSectorColonia(s[0].id);
    });
  };

  useEffect(() => {
    cargarTodo();
  }, [sectorFiltro]);

  const descargarExportacion = async (formato: "csv" | "xml") => {
    const token = sessionStorage.getItem("csj_token");
    const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    const res = await fetch(`${apiBase}/admin/exportar?formato=${formato}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reportes_juarez.${formato}`;
    a.click();
  };

  const cambiarRol = async (id: number, rol: RolUsuario) => {
    try {
      await apiFetch(`/admin/usuarios/${id}/rol`, {
        method: "PATCH",
        body: JSON.stringify({ rol }),
      });
      cargarTodo();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const crearColonia = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevaColonia.trim()) return;
    try {
      await apiFetch("/catalogos/colonias", {
        method: "POST",
        body: JSON.stringify({
          nombre: nuevaColonia.trim(),
          codigo_postal: nuevoCp.trim() || null,
          sector_id: Number(sectorColonia),
        }),
      });
      setNuevaColonia("");
      setNuevoCp("");
      cargarTodo();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const maxSem = tablero ? Math.max(1, ...tablero.tendencia_12_semanas.map((s) => s.total)) : 1;

  return (
    <div className="container page-content">
      <div className="section-header">
        <h1>Tablero de Indicadores y Administración</h1>
        <div className="btn-group">
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => descargarExportacion("csv")}>
            Exportar CSV
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => descargarExportacion("xml")}>
            Exportar XML
          </button>
        </div>
      </div>

      {/* Filtro por sector HU-07.1 CA5 */}
      <div className="form-group max-w-sm">
        <label htmlFor="sec-filtro">Filtrar indicadores por sector</label>
        <select id="sec-filtro" value={sectorFiltro} onChange={(e) => setSectorFiltro(e.target.value)}>
          <option value="">Todos los sectores de Juárez</option>
          {sectores.map((s) => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
          ))}
        </select>
      </div>

      {tablero && (
        <>
          <section className="kpi-grid" aria-label="Indicadores clave">
            <div className="kpi-card">
              <span className="kpi-label">Total de reportes</span>
              <strong className="kpi-value">{tablero.total_reportes}</strong>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Baches / Pavimento</span>
              <strong className="kpi-value">{tablero.por_categoria.bache}</strong>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Encharcamientos</span>
              <strong className="kpi-value">{tablero.por_categoria.encharcamiento}</strong>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Tiempo promedio reparación</span>
              <strong className="kpi-value">{tablero.tiempo_promedio_reparacion_dias} días</strong>
            </div>
          </section>

          {/* Gráfica últimas 12 semanas HU-07.1 CA3 */}
          <section className="panel-box">
            <h2>Reportes recibidos por semana (Últimas 12 semanas)</h2>
            <div className="bar-chart" role="img" aria-label="Gráfica de barras de reportes semanales">
              {tablero.tendencia_12_semanas.map((s) => (
                <div key={s.semana} className="bar-col">
                  <span className="bar-num">{s.total}</span>
                  <div
                    className="bar-fill"
                    style={{ height: `${Math.max(8, (s.total / maxSem) * 140)}px` }}
                  />
                  <span className="bar-label">{s.semana}</span>
                </div>
              ))}
            </div>
          </section>

          <div className="two-cols">
            <section className="panel-box">
              <h2>Top 10 colonias con más baches abiertos</h2>
              <table className="data-table">
                <thead>
                  <tr><th>Colonia</th><th>Abiertos</th><th>Longevidad prom.</th></tr>
                </thead>
                <tbody>
                  {tablero.top_10_colonias.map((c) => (
                    <tr key={c.colonia}>
                      <td>{c.colonia}</td>
                      <td>{c.baches_abiertos}</td>
                      <td>{c.longevidad_promedio_dias} d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="panel-box">
              <h2>Top 10 baches abiertos con mayor longevidad</h2>
              <table className="data-table">
                <thead>
                  <tr><th>Folio</th><th>Colonia</th><th>Días</th></tr>
                </thead>
                <tbody>
                  {tablero.top_10_longevidad.map((b) => (
                    <tr key={b.folio}>
                      <td>{b.folio}</td>
                      <td>{b.colonia}</td>
                      <td>{b.dias} d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        </>
      )}

      {/* Administración de Colonias HU-06.1 */}
      <section className="panel-box">
        <h2>Catálogo de Colonias ({colonias.length})</h2>
        <form onSubmit={crearColonia} className="inline-form mb-1">
          <input
            type="text"
            placeholder="Nombre de la colonia"
            value={nuevaColonia}
            onChange={(e) => setNuevaColonia(e.target.value)}
            aria-label="Nombre de la colonia"
          />
          <input
            type="text"
            placeholder="Código Postal"
            value={nuevoCp}
            onChange={(e) => setNuevoCp(e.target.value)}
            aria-label="Código Postal"
          />
          <select
            value={sectorColonia}
            onChange={(e) => setSectorColonia(Number(e.target.value))}
            aria-label="Sector"
          >
            {sectores.map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </select>
          <button type="submit" className="btn btn-primary btn-sm">Agregar colonia</button>
        </form>
      </section>

      {/* Administración de Usuarios y Roles HU-06.2 */}
      <section className="panel-box">
        <h2>Usuarios y Roles</h2>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr><th>Nombre</th><th>Correo</th><th>Rol actual</th><th>Cambiar rol</th></tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id}>
                  <td>{u.nombre}</td>
                  <td>{u.correo}</td>
                  <td>{u.rol}</td>
                  <td>
                    <select
                      aria-label={`Rol para ${u.nombre}`}
                      value={u.rol}
                      onChange={(e) => cambiarRol(u.id, e.target.value as RolUsuario)}
                    >
                      <option value="ciudadano">Ciudadano</option>
                      <option value="moderador">Moderador</option>
                      <option value="coordinador">Coordinador</option>
                      <option value="enlace_municipal">Enlace municipal</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};