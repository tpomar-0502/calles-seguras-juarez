import React, { useEffect, useRef } from "react";
import L from "leaflet";
import { Reporte } from "../types";

interface Props {
  reportes: Reporte[];
  center?: [number, number];
  selectable?: boolean;
  onSelectCoords?: (lat: number, lon: number) => void;
}

export const MapView: React.FC<Props> = ({
  reportes,
  center = [31.715, -106.445],
  selectable = false,
  onSelectCoords,
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current).setView(center, 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;
    markersLayerRef.current = layerGroup;

    if (selectable && onSelectCoords) {
      map.on("click", (e: L.LeafletMouseEvent) => {
        onSelectCoords(Number(e.latlng.lat.toFixed(6)), Number(e.latlng.lng.toFixed(6)));
      });
    }

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;
    markersLayerRef.current.clearLayers();

    reportes.forEach((rep) => {
      const color = rep.categoria === "bache" ? "#d97706" : "#0284c7";
      const marker = L.circleMarker([rep.latitud, rep.longitud], {
        radius: 8,
        fillColor: color,
        color: "#0f172a",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      });

      marker.bindPopup(
        `<strong>${rep.folio}</strong> (${rep.categoria.toUpperCase()})<br/>` +
          `${rep.calle}<br/>Estado: ${rep.estado}<br/>` +
          `<a href="/reportes/${rep.folio}">Ver detalle</a>`
      );
      marker.addTo(markersLayerRef.current!);
    });
  }, [reportes]);

  useEffect(() => {
    if (mapInstanceRef.current && center) {
      mapInstanceRef.current.setView(center, selectable ? 15 : 12);
    }
  }, [center, selectable]);

  return (
    <div
      ref={mapContainerRef}
      className="leaflet-box"
      role="region"
      aria-label="Mapa interactivo de reportes en Ciudad Juárez"
    />
  );
};