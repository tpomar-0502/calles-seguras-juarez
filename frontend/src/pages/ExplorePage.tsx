import React, { useEffect, useRef, useState } from "react";
import { apiFetch } from "../api/client";
import { MapView } from "../components/MapView";
import { ReportCard } from "../components/ReportCard";
import { WeatherBanner } from "../components/WeatherBanner";
import { Colonia, PaginatedReportes, Reporte } from "../types";

export const ExplorePage: React.FC = () => {
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [colonias, setColonias] = useState<Colonia[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros HU-04.2
  const [categoria, setCategoria] = useState("");
  const [coloniaId, setColoniaId] = useState("");
  const [severidad, setSeveridad] = useState("");
  const [busqueda, setBusqueda] = useState("");

  // Consulta "Cómo está mi zona" HU-04.3
  const zonaRef = useRef<HTMLElement | null>(null);
  const [direccionZona, setDireccionZona] = useState("");
  const [reportesZona, setReportesZona] = useState<Reporte[] | null>(null);
  const [msgZona, setMsgZona] = useState<string | null>(null);
  const [centroMapa, setCentroMapa] = useState<[number, number]>([31.715, -106.445]);

  useEffect(() => {
    apiFetch<Colonia[]>("/catalogos/colonias").then(setColonias).catch(() => {});
  }, []);

  const cargarReportes = () => {
    setCargando(true);
    setError(null);
    const params = new URLSearchParams();
    params.set("pagina", String(pagina));
    params.set("tamano_pagina", "20");
    if (categoria) params.set("categoria", categoria);
    if (coloniaId) params.set("colonia_id", coloniaId);
    if (severidad) params.set("severidad", severidad);
    if (busqueda.trim()) params.set("q", busqueda.trim());

    apiFetch<PaginatedReportes>(`/reportes?${params.toString()}`)
      .then((res) => {
        setReportes(res.items);
        setTotal(res.total);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    cargarReportes();
  }, [pagina, categoria, coloniaId, severidad]);

  const limpiarFiltros = () => {
    setCategoria("");
    setColoniaId("");
    setSeveridad("");
    setBusqueda("");
    setPagina(1);
  };

  const buscarPorDireccion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!direccionZona.trim()) return;
    setMsgZona("Buscando dirección en Juárez...");
    try {
      const geo = await apiFetch<{ latitud: number; longitud: number; en_juarez: boolean }>(
        `/servicios/geocodificar?direccion=${encodeURIComponent(direccionZona)}`
      );
      if (!geo.en_juarez) {
        setMsgZona("La ubicación encontrada está fuera de Ciudad Juárez.");
        return;
      }
      setCentroMapa([geo.latitud, geo.longitud]);
      const cercanos = await apiFetch<Reporte[]>(
        `/reportes/cerca?lat=${geo.latitud}&lon=${geo.longitud}&radio_metros=1000`
      );
      setReportesZona(cercanos);
      setMsgZona(
        cercanos.length > 0
          ? `Se encontraron ${cercanos.length} reportes activos a 1 km o menos.`
          : "No hay baches ni encharcamientos activos en un radio de 1 km."
      );
    } catch (err) {
      setMsgZona((err as Error).message);
      setReportesZona(null);
    }
  };

  const usarMiUbicacion = () => {
    if (!navigator.geolocation) {
      setMsgZona("Tu navegador no soporta geolocalización.");
      return;
    }
    setMsgZona("Obteniendo tu ubicación actual...");
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setCentroMapa([latitude, longitude]);
        try {
          const cercanos = await apiFetch<Reporte[]>(
            `/reportes/cerca?lat=${latitude}&lon=${longitude}&radio_metros=1000`
          );
          setReportesZona(cercanos);
          setMsgZona(`Reportes activos a 1 km de tu ubicación: ${cercanos.length}`);
        } catch (err) {
          setMsgZona((err as Error).message);
        }
      },
      () => setMsgZona("No se pudo obtener el permiso de ubicación.")
    );
  };

  const totalPaginas = Math.max(1, Math.ceil(total / 20));

  return (
    <div className="container page-content">
      <WeatherBanner onIrAMiZona={() => zonaRef.current?.scrollIntoView({ behavior: "smooth" })} />

      <section className="hero-section">
        <h1>Consulta ciudadana de baches y encharcamientos en Ciudad Juárez</h1>
        <p>
          Verifica el estado de las vialidades antes de salir. Todos los reportes públicos protegen la identidad de quienes reportan.
        </p>
      </section>

      {/* Sección HU-04.3: ¿Cómo está mi zona? */}
      <section ref={zonaRef} className="panel-box" aria-labelledby="titulo-mi-zona">
        <h2 id="titulo-mi-zona">¿Cómo está mi zona? (Radio de 1 km)</h2>
        <form onSubmit={buscarPorDireccion} className="inline-form">
          <div className="form-group flex-grow">
            <label htmlFor="dir-zona">Calle, cruce o colonia de referencia</label>
            <input
              id="dir-zona"
              type="text"
              placeholder="Ej. Av. Tecnológico y Ejército Nacional"
              value={direccionZona}
              onChange={(e) => setDireccionZona(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary">Buscar zona</button>
          <button type="button" onClick={usarMiUbicacion} className="btn btn-secondary">
            Usar mi GPS
          </button>
        </form>

        {msgZona && <p className="status-note">{msgZona}</p>}

        {reportesZona && reportesZona.length > 0 && (
          <div className="cards-grid mt-1">
            {reportesZona.map((r) => (
              <ReportCard key={r.id} reporte={r} />
            ))}
          </div>
        )}
      </section>

      {/* Mapa interactivo HU-04.5 */}
      <section className="panel-box" aria-labelledby="titulo-mapa">
        <h2 id="titulo-mapa">Mapa vial de reportes activos</h2>
        <p className="legend-row">
          <span><i className="dot dot-bache" aria-hidden="true" /> Bache / Pavimento</span>
          <span><i className="dot dot-agua" aria-hidden="true" /> Encharcamiento activo</span>
        </p>
        <MapView reportes={reportes} center={centroMapa} />
      </section>

      {/* Filtros y listado paginado HU-04.1 y HU-04.2 */}
      <section className="panel-box" aria-labelledby="titulo-listado">
        <h2 id="titulo-listado">Reportes activos ({total})</h2>

        <form
          className="filters-grid"
          onSubmit={(e) => {
            e.preventDefault();
            setPagina(1);
            cargarReportes();
          }}
        >
          <div className="form-group">
            <label htmlFor="f-q">Buscar calle o folio</label>
            <input
              id="f-q"
              type="text"
              placeholder="BCH-2026... o Av. 16 de Septiembre"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="f-cat">Tipo de reporte</label>
            <select id="f-cat" value={categoria} onChange={(e) => { setCategoria(e.target.value); setPagina(1); }}>
              <option value="">Todos</option>
              <option value="bache">Bache / Pavimento</option>
              <option value="encharcamiento">Encharcamiento</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="f-col">Colonia</label>
            <select id="f-col" value={coloniaId} onChange={(e) => { setColoniaId(e.target.value); setPagina(1); }}>
              <option value="">Todas las colonias</option>
              {colonias.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="f-sev">Severidad (Baches)</label>
            <select id="f-sev" value={severidad} onChange={(e) => { setSeveridad(e.target.value); setPagina(1); }}>
              <option value="">Todas</option>
              <option value="Baja">Baja</option>
              <option value="Media">Media</option>
              <option value="Alta">Alta</option>
            </select>
          </div>

          <div className="filter-buttons">
            <button type="submit" className="btn btn-primary">Filtrar</button>
            <button type="button" onClick={limpiarFiltros} className="btn btn-secondary">Limpiar</button>
          </div>
        </form>

        {cargando && <p className="state-msg">Cargando reportes de Ciudad Juárez...</p>}
        {error && <p className="error-box" role="alert">Error: {error}</p>}

        {!cargando && !error && reportes.length === 0 && (
          <div className="empty-box">
            <p>Ningún reporte coincide con los filtros seleccionados.</p>
            <button type="button" onClick={limpiarFiltros} className="btn btn-primary btn-sm">
              Limpiar filtros
            </button>
          </div>
        )}

        {!cargando && reportes.length > 0 && (
          <>
            <div className="cards-grid">
              {reportes.map((r) => (
                <ReportCard key={r.id} reporte={r} />
              ))}
            </div>

            <nav className="pagination" aria-label="Paginación de reportes">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={pagina <= 1}
                onClick={() => setPagina((p) => p - 1)}
              >
                Anterior
              </button>
              <span>Página {pagina} de {totalPaginas}</span>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={pagina >= totalPaginas}
                onClick={() => setPagina((p) => p + 1)}
              >
                Siguiente
              </button>
            </nav>
          </>
        )}
      </section>
    </div>
  );
};