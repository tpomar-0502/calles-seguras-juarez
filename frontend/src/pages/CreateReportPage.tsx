import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";
import { MapView } from "../components/MapView";
import {
  CategoriaReporte,
  Colonia,
  NivelAgua,
  Reporte,
  SeveridadBache,
  TipoDanoBache,
} from "../types";

export const CreateReportPage: React.FC = () => {
  const navigate = useNavigate();
  const [colonias, setColonias] = useState<Colonia[]>([]);

  // Campos comunes
  const [categoria, setCategoria] = useState<CategoriaReporte>("bache");
  const [calle, setCalle] = useState("");
  const [referencia, setReferencia] = useState("");
  const [coloniaId, setColoniaId] = useState<number>(1);
  const [latitud, setLatitud] = useState<number>(31.7385);
  const [longitud, setLongitud] = useState<number>(-106.485);
  const [descripcion, setDescripcion] = useState("");

  // Campos dinámicos Bache (HU-02.2)
  const [tipoDano, setTipoDano] = useState<TipoDanoBache>("bache");
  const [tamanoBache, setTamanoBache] = useState("mediano");
  const [profundidadAprox, setProfundidadAprox] = useState("10 cm");
  const [carrilAfectado, setCarrilAfectado] = useState("Derecho");
  const [severidad, setSeveridad] = useState<SeveridadBache>("Media");
  const [alcantarillaSenalizada, setAlcantarillaSenalizada] = useState<boolean>(false);

  // Campos dinámicos Encharcamiento (HU-03.1)
  const [nivelAgua, setNivelAgua] = useState<NivelAgua>("cubre un carril");
  const [riesgoVehiculos, setRiesgoVehiculos] = useState<boolean>(false);

  // Control de duplicados (HU-02.3)
  const [duplicados, setDuplicados] = useState<Reporte[]>([]);
  const [ignorarDuplicados, setIgnorarDuplicados] = useState(false);

  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Colonia[]>("/catalogos/colonias")
      .then((cols) => {
        setColonias(cols);
        if (cols.length > 0) setColoniaId(cols[0].id);
      })
      .catch(() => {});
  }, []);

  const usarGPS = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      setLatitud(Number(pos.coords.latitude.toFixed(6)));
      setLongitud(Number(pos.coords.longitude.toFixed(6)));
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (calle.trim().length < 3) {
      setError("Indica el nombre de la calle.");
      return;
    }
    if (descripcion.trim().length < 5 || descripcion.length > 500) {
      setError("La descripción debe tener entre 5 y 500 caracteres.");
      return;
    }

    // Verificar duplicados cercanos (30m bache / 50m encharcamiento) si aún no se confirmó crear nuevo
    if (!ignorarDuplicados) {
      try {
        const cercanos = await apiFetch<Reporte[]>(
          `/reportes/verificar-duplicados?categoria=${categoria}&lat=${latitud}&lon=${longitud}`
        );
        if (cercanos.length > 0) {
          setDuplicados(cercanos);
          return;
        }
      } catch {
        // continuar si falla la verificación
      }
    }

    setEnviando(true);
    try {
      const payload: Record<string, unknown> = {
        categoria,
        calle: calle.trim(),
        referencia: referencia.trim() || null,
        latitud,
        longitud,
        colonia_id: Number(coloniaId),
        descripcion: descripcion.trim(),
      };

      if (categoria === "bache") {
        payload.tipo_dano = tipoDano;
        payload.severidad = tipoDano === "alcantarilla_sin_tapa" ? "Alta" : severidad;
        if (tipoDano === "bache") {
          payload.tamano_bache = tamanoBache;
          payload.profundidad_aprox = profundidadAprox;
          payload.carril_afectado = carrilAfectado;
        }
        if (tipoDano === "alcantarilla_sin_tapa") {
          payload.alcantarilla_senalizada = alcantarillaSenalizada;
        }
      } else {
        payload.nivel_agua = nivelAgua;
        if (nivelAgua === "intransitable") {
          payload.riesgo_vehiculos_personas = riesgoVehiculos;
        }
      }

      const creado = await apiFetch<Reporte>("/reportes", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      navigate(`/reportes/${creado.folio}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  const confirmarExistente = async (folio: string) => {
    try {
      await apiFetch(`/reportes/${folio}/interaccion`, {
        method: "POST",
        body: JSON.stringify({ tipo: "confirmacion" }),
      });
      navigate(`/reportes/${folio}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="container page-content">
      <h1>Registrar nuevo reporte vial</h1>

      {duplicados.length > 0 && (
        <section className="alert-duplicate" role="alert">
          <h2>Ya existe un reporte abierto muy cerca de este punto</h2>
          <p>Para evitar duplicados, puedes confirmar el reporte existente en lugar de generar otro folio:</p>
          {duplicados.map((d) => (
            <div key={d.id} className="dup-item">
              <strong>{d.folio}</strong> — {d.calle} (a {d.distancia_metros} m)
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => confirmarExistente(d.folio)}
              >
                Confirmar este reporte
              </button>
            </div>
          ))}
          <button
            type="button"
            className="btn btn-secondary btn-sm mt-1"
            onClick={() => {
              setIgnorarDuplicados(true);
              setDuplicados([]);
            }}
          >
            Es un daño distinto, continuar con mi reporte nuevo
          </button>
        </section>
      )}

      <form onSubmit={handleSubmit} className="panel-box form-stack">
        {error && <p className="error-box" role="alert">{error}</p>}

        <div className="form-group">
          <label htmlFor="rep-cat">¿Qué deseas reportar?</label>
          <select
            id="rep-cat"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value as CategoriaReporte)}
          >
            <option value="bache">Bache o daño en pavimento</option>
            <option value="encharcamiento">Encharcamiento / Inundación</option>
          </select>
        </div>

        <div className="two-cols">
          <div className="form-group">
            <label htmlFor="rep-calle">Calle y número o cruce *</label>
            <input
              id="rep-calle"
              type="text"
              required
              value={calle}
              onChange={(e) => setCalle(e.target.value)}
              placeholder="Ej. Av. Hermanos Escobar #2300"
            />
          </div>

          <div className="form-group">
            <label htmlFor="rep-col">Colonia *</label>
            <select
              id="rep-col"
              value={coloniaId}
              onChange={(e) => setColoniaId(Number(e.target.value))}
            >
              {colonias.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Ubicación en el mapa (haz clic en el punto exacto o usa tu GPS)</label>
          <div className="inline-form mb-1">
            <input type="number" step="any" value={latitud} onChange={(e) => setLatitud(Number(e.target.value))} aria-label="Latitud" />
            <input type="number" step="any" value={longitud} onChange={(e) => setLongitud(Number(e.target.value))} aria-label="Longitud" />
            <button type="button" className="btn btn-secondary btn-sm" onClick={usarGPS}>
              Usar GPS
            </button>
          </div>
          <MapView
            reportes={[]}
            center={[latitud, longitud]}
            selectable
            onSelectCoords={(lat, lon) => {
              setLatitud(lat);
              setLongitud(lon);
            }}
          />
        </div>

        {/* Campos dinámicos según categoría */}
        {categoria === "bache" ? (
          <>
            <div className="form-group">
              <label htmlFor="tipo-dano">Tipo de daño en pavimento *</label>
              <select
                id="tipo-dano"
                value={tipoDano}
                onChange={(e) => setTipoDano(e.target.value as TipoDanoBache)}
              >
                <option value="bache">Bache</option>
                <option value="hundimiento">Hundimiento</option>
                <option value="grieta">Grieta</option>
                <option value="alcantarilla_sin_tapa">Alcantarilla sin tapa</option>
              </select>
            </div>

            {tipoDano === "bache" && (
              <div className="three-cols">
                <div className="form-group">
                  <label htmlFor="tam-bache">Tamaño aproximado *</label>
                  <select id="tam-bache" value={tamanoBache} onChange={(e) => setTamanoBache(e.target.value)}>
                    <option value="chico">Chico (menos de 30 cm)</option>
                    <option value="mediano">Mediano (30 cm a 1 m)</option>
                    <option value="grande">Grande (más de 1 m)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="prof-bache">Profundidad aproximada *</label>
                  <input
                    id="prof-bache"
                    type="text"
                    required
                    value={profundidadAprox}
                    onChange={(e) => setProfundidadAprox(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="carril-bache">Carril afectado *</label>
                  <select id="carril-bache" value={carrilAfectado} onChange={(e) => setCarrilAfectado(e.target.value)}>
                    <option value="Derecho">Derecho</option>
                    <option value="Central">Central</option>
                    <option value="Izquierdo">Izquierdo</option>
                    <option value="Todos">Todos</option>
                  </select>
                </div>
              </div>
            )}

            {tipoDano === "alcantarilla_sin_tapa" ? (
              <div className="form-group">
                <p className="status-note">Severidad asignada automáticamente: <strong>Alta</strong></p>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={alcantarillaSenalizada}
                    onChange={(e) => setAlcantarillaSenalizada(e.target.checked)}
                  />
                  El punto cuenta con alguna señalización preventiva
                </label>
              </div>
            ) : (
              <div className="form-group">
                <label htmlFor="sev-bache">Severidad estimada</label>
                <select id="sev-bache" value={severidad} onChange={(e) => setSeveridad(e.target.value as SeveridadBache)}>
                  <option value="Baja">Baja</option>
                  <option value="Media">Media</option>
                  <option value="Alta">Alta</option>
                </select>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="form-group">
              <label htmlFor="nivel-agua">Nivel de agua acumulada *</label>
              <select
                id="nivel-agua"
                value={nivelAgua}
                onChange={(e) => setNivelAgua(e.target.value as NivelAgua)}
              >
                <option value="a un lado de la calle">A un lado de la calle</option>
                <option value="cubre un carril">Cubre un carril</option>
                <option value="a media llanta">A media llanta</option>
                <option value="intransitable">Intransitable</option>
              </select>
            </div>

            {nivelAgua === "intransitable" && (
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={riesgoVehiculos}
                    onChange={(e) => setRiesgoVehiculos(e.target.checked)}
                  />
                  Hay vehículos varados o personas en riesgo en el punto
                </label>
              </div>
            )}
          </>
        )}

        <div className="form-group">
          <label htmlFor="rep-ref">Referencia cercana (opcional)</label>
          <input
            id="rep-ref"
            type="text"
            value={referencia}
            onChange={(e) => setReferencia(e.target.value)}
            placeholder="Frente a parque, escuela o comercio"
          />
        </div>

        <div className="form-group">
          <label htmlFor="rep-desc">Descripción detallada * ({descripcion.length}/500)</label>
          <textarea
            id="rep-desc"
            rows={3}
            maxLength={500}
            required
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={enviando}>
          {enviando ? "Enviando reporte..." : "Enviar reporte ciudadano"}
        </button>
      </form>
    </div>
  );
};