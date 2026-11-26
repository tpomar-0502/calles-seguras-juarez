# GEMINI.md — Contexto del Proyecto: Calles Seguras Juárez

## Descripción General
**Calles Seguras Juárez** es una plataforma web cívica para el reporte, geolocalización, moderación y seguimiento de incidencias urbanas en **Ciudad Juárez, Chihuahua** (baches, alumbrado público, semaforización, fugas de agua, acumulación de basura y señalización vial).

* **Frontend (Producción):** `https://calles-seguras-juarez-sooty.vercel.app/`
* **Backend API (Producción):** `https://calles-seguras-juarez-api-i2sn.onrender.com/api/v1`
* **Zona Horaria Oficial:** `America/Ciudad_Juarez`

---

## Arquitectura y Stack Tecnológico

* **Frontend (`/frontend`):** React 18 + TypeScript + Vite. Estilizado responsivo (*mobile-first*), visualización de mapas interactivos, gráficas estadísticas de 12 semanas y enrutamiento SPA configurado en `frontend/vercel.json`.
  * Variable de entorno clave: `VITE_API_URL` (debe apuntar a la URL base de la API incluyendo `/api/v1`).
* **Backend (`/backend`):** Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy. Autenticación JWT (`Bearer`) con control de acceso basado en roles (RBAC).
  * Variables de entorno clave: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `TIMEZONE`.
* **Base de Datos (`/db`):** PostgreSQL 16 (Neon en producción / contenedor en local). Inicializada mediante `db/seed.py` con 4 sectores urbanos, 24 colonias reales de Ciudad Juárez y 500 reportes históricos distribuidos en 12 semanas.

---

## Roles y Control de Acceso (RBAC)

1. **`ciudadano`:** Consulta mapa y estadísticas públicas, registra nuevos reportes urbanos y consulta el historial por folio.
2. **`moderador`:** Revisa reportes entrantes, detecta duplicados, valida evidencia y aprueba o rechaza publicaciones.
3. **`coordinador`:** Accede al tablero analítico completo, asigna prioridades, gestiona usuarios/sectores y supervisa métricas operativas.
4. **`enlace` (Enlace Municipal):** Da seguimiento interinstitucional, actualiza estatus de atención (`en_proceso`, `resuelto`) y exporta métricas.

---

## Convenciones de Desarrollo

* **Idioma:** Todo el código de dominio, mensajes de interfaz, documentación y commits deben redactarse en **español** (siguiendo *Conventional Commits*: `feat:`, `fix:`, `docs:`, `chore:`).
* **Privacidad (LFPDPPP):** Los endpoints públicos nunca deben exponer nombres, correos electrónicos ni identificadores personales de los ciudadanos que crean reportes.
* **Rutas de API:** Todos los endpoints están versionados bajo el prefijo `/api/v1` (ej. `/api/v1/auth/login`, `/api/v1/reportes`, `/api/v1/colonias`).
* **Integridad de Archivos:** Todos los archivos de código, configuración (`.json`, `.yml`) y documentación (`.md`) deben guardarse en **UTF-8 sin BOM**.

---

## Comandos Frecuentes

* **Levantar entorno completo con Docker:** `docker compose up --build`
* **Ejecutar backend en desarrollo:** `cd backend && uvicorn app.main:app --reload --port 8000`
* **Ejecutar frontend en desarrollo:** `cd frontend && npm run dev`
* **Poblar base de datos:** `cd backend && $env:PYTHONPATH="."; python ../db/seed.py`