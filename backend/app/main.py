from app.core.config import settings
from app.routers import admin_catalogos, auth, reportes, servicios
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API REST para reporte y seguimiento de baches y encharcamientos en Ciudad Juárez.",
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(reportes.router, prefix=settings.API_V1_STR)
app.include_router(admin_catalogos.router, prefix=settings.API_V1_STR)
app.include_router(servicios.router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "servicio": settings.PROJECT_NAME}