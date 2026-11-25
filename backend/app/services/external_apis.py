import time

import httpx
from app.core.config import settings

# Coordenadas centrales de Ciudad Juárez, Chihuahua
JUAREZ_LAT = 31.6904
JUAREZ_LON = -106.4245

_weather_cache: dict = {"timestamp": 0.0, "data": None}
CACHE_TTL_SECONDS = 3600  # 1 hora (HU-08.1 CA3)


def esta_en_juarez(lat: float, lon: float) -> bool:
    return (
        settings.JUAREZ_LAT_MIN <= lat <= settings.JUAREZ_LAT_MAX
        and settings.JUAREZ_LON_MIN <= lon <= settings.JUAREZ_LON_MAX
    )


async def obtener_pronostico_lluvia() -> dict:
    ahora = time.time()
    if _weather_cache["data"] and (ahora - _weather_cache["timestamp"] < CACHE_TTL_SECONDS):
        return _weather_cache["data"]

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={JUAREZ_LAT}&longitude={JUAREZ_LON}"
        f"&hourly=precipitation_probability&forecast_hours=12&timezone=America%2FCiudad_Juarez"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            probs = payload.get("hourly", {}).get("precipitation_probability", [])
            max_prob = max(probs) if probs else 0
            resultado = {
                "disponible": True,
                "hay_lluvia": max_prob >= 30,
                "probabilidad_maxima": max_prob,
                "mensaje": (
                    f"Probabilidad de lluvia del {max_prob}% en Ciudad Juárez en las próximas 12 horas."
                    if max_prob >= 30
                    else "Sin pronóstico de lluvia relevante en las próximas 12 horas."
                ),
            }
            _weather_cache["timestamp"] = ahora
            _weather_cache["data"] = resultado
            return resultado
    except Exception:
        return {
            "disponible": False,
            "hay_lluvia": False,
            "probabilidad_maxima": None,
            "mensaje": "Pronóstico no disponible",
        }


async def geocodificar_direccion(direccion: str) -> dict | None:
    query = f"{direccion}, Ciudad Juárez, Chihuahua, México"
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "CallesSegurasJuarez-ITCJ/1.0 (educativo)"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params={"q": query, "format": "json", "limit": 1}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return {
                "latitud": lat,
                "longitud": lon,
                "display_name": data[0].get("display_name", direccion),
                "en_juarez": esta_en_juarez(lat, lon),
            }
    except Exception:
        return None