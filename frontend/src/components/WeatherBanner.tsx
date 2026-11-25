import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { ClimaJuarez } from "../types";

interface Props {
  onIrAMiZona: () => void;
}

export const WeatherBanner: React.FC<Props> = ({ onIrAMiZona }) => {
  const [clima, setClima] = useState<ClimaJuarez | null>(null);

  useEffect(() => {
    apiFetch<ClimaJuarez>("/servicios/clima")
      .then(setClima)
      .catch(() =>
        setClima({
          disponible: false,
          hay_lluvia: false,
          probabilidad_maxima: null,
          mensaje: "Pronóstico no disponible",
        })
      );
  }, []);

  if (!clima) return null;

  if (!clima.disponible) {
    return (
      <aside className="banner banner-neutral" role="status">
        <span>Clima en Juárez: {clima.mensaje}</span>
      </aside>
    );
  }

  if (!clima.hay_lluvia) return null;

  return (
    <aside className="banner banner-rain" role="alert">
      <div>
        <strong>Alerta de lluvia en Juárez:</strong> {clima.mensaje}
      </div>
      <button type="button" className="btn btn-dark btn-sm" onClick={onIrAMiZona}>
        Revisar mi zona antes de salir
      </button>
    </aside>
  );
};