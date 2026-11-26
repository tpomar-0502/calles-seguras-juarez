# Calles Seguras Juárez

Plataforma web cívica de participación ciudadana, monitoreo geoespacial y gestión operativa para el reporte y seguimiento de incidencias urbanas en **Ciudad Juárez, Chihuahua** (baches, alumbrado público, semaforización, fugas de agua, acumulación de basura y señalización vial).

---

## Despliegue en Producción

* **Aplicación Web (Frontend):** [https://calles-seguras-juarez-sooty.vercel.app/](https://calles-seguras-juarez-sooty.vercel.app/)
* **API REST (Backend):** [https://calles-seguras-juarez-api-i2sn.onrender.com](https://calles-seguras-juarez-api-i2sn.onrender.com)
* **Documentación Interactiva (Swagger UI):** [https://calles-seguras-juarez-api-i2sn.onrender.com/docs](https://calles-seguras-juarez-api-i2sn.onrender.com/docs)

> **Nota sobre instancia gratuita:** El backend en Render entra en suspensión tras 15 minutos de inactividad; la primera petición puede tardar ~25–30 segundos en responder mientras se reactiva el contenedor.

---

## Arquitectura del Sistema

El proyecto implementa una arquitectura desacoplada de tres capas:

1. **Capa de Presentación (Vercel):** SPA desarrollada en **React + TypeScript + Vite**, con mapas interactivos, visualización estadística de las últimas 12 semanas, filtros por colonia/sector/categoría y diseño responsivo (*mobile-first*).
2. **Capa de Lógica de Negocio (Render):** API REST construida con **FastAPI (Python 3.12)**, validación de esquemas con **Pydantic**, ORM **SQLAlchemy**, autenticación basada en **JWT** y control de acceso basado en roles (RBAC).
3. **Capa de Persistencia (Neon):** Base de datos relacional **PostgreSQL** en la nube, inicializada con 4 sectores administrativos, 24 colonias reales de Ciudad Juárez y 500 reportes distribuidos en 12 semanas.

---

## Cuentas de Prueba (`db/seed.py`)

El entorno de producción cuenta con 5 usuarios precargados para validar cada nivel de permisos:

| Rol | Correo Electrónico | Contraseña | Permisos Principales |
| :--- | :--- | :--- | :--- |
| **Ciudadano** | `ciudadano@callesjuarez.org` | `Juarez2026!` | Crear reportes, consultar mapa público y seguimiento por folio. |
| **Ciudadano (2)** | `vecino2@callesjuarez.org` | `Juarez2026!` | Crear reportes y confirmar incidencias vecinales. |
| **Moderador** | `moderador@callesjuarez.org` | `Juarez2026!` | Validar reportes entrantes, filtrar duplicados y cambiar estatus inicial. |
| **Coordinador** | `coordinador@callesjuarez.org` | `Juarez2026!` | Acceso al tablero analítico, asignación de prioridades y gestión integral. |
| **Enlace Municipal** | `enlace@juarez.gob.mx` | `Juarez2026!` | Seguimiento interinstitucional, resolución de incidencias y exportación de métricas. |

---

## Instalación y Ejecución Local

### Opción A: Con Docker Compose

```bash
git clone [https://github.com/OmarPadilla05/calles-seguras-juarez.git](https://github.com/OmarPadilla05/calles-seguras-juarez.git)
cd calles-seguras-juarez
docker compose up --build
```

* **Frontend:** `http://localhost:5173`
* **Backend API:** `http://localhost:8000` (`/docs` para Swagger)

### Opción B: Ejecución Manual (Desarrollo)

**1. Backend (FastAPI):**

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Poblar base de datos (opcional en local):**

```bash
cd backend
$env:PYTHONPATH="."
python ../db/seed.py
```

**3. Frontend (React + Vite):**

```bash
cd frontend
npm install
npm run dev
```

---

## Estructura del Repositorio

```text
calles-seguras-juarez/
├── backend/            # API FastAPI, modelos SQLAlchemy, esquemas Pydantic y Dockerfile
├── frontend/           # Aplicación React + TypeScript + Vite y configuración vercel.json
├── db/                 # Script de carga inicial (seed.py) y esquemas SQL
├── docs/               # Documentación técnica, autoevaluación y reporte final (PDF)
├── docker-compose.yml  # Orquestación local de servicios
├── GEMINI.md           # Contexto técnico del proyecto para asistentes de IA
├── AI_USAGE.md         # Bitácora de uso responsable de Inteligencia Artificial
└── README.md           # Documentación general del proyecto
```

---

## Privacidad y Cumplimiento

Los reportes publicados en la vista ciudadana se muestran de forma anónima conforme a los principios de protección de datos personales (**LFPDPPP**), resguardando la identidad de los denunciantes mientras se transparenta la atención urbana por colonia y sector.

---

## Autores

* **Omar Padilla Torres** — Instituto Tecnológico de Ciudad Juárez (ITCJ)
* **Daniel Valadez Macías** — Instituto Tecnológico de Ciudad Juárez (ITCJ)