from app.services.external_apis import geocodificar_direccion, obtener_pronostico_lluvia
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/servicios", tags=["Servicios Externos"])


@router.get("/clima")
async def consultar_clima_juarez():
    """HU-08.1: Consulta pronóstico de lluvia en Ciudad Juárez desde Open-Meteo."""
    return await obtener_pronostico_lluvia()


@router.get("/geocodificar")
async def buscar_ubicacion(direccion: str):
    """HU-02.1 y HU-04.3: Convierte una dirección en Juárez a coordenadas vía Nominatim."""
    res = await geocodificar_direccion(direccion)
    if not res:
        raise HTTPException(status_code=404, detail="No se encontró la dirección. Intenta con calle y colonia.")
    return res