# Autoevaluación del Proyecto — Calles Seguras Juárez

* **Institución:** Instituto Tecnológico de Ciudad Juárez (ITCJ)
* **Integrantes:** Omar Padilla Torres y Daniel Valadez Macías
* **URL en Producción:** [https://calles-seguras-juarez-sooty.vercel.app/](https://calles-seguras-juarez-sooty.vercel.app/)
* **API en Producción:** [https://calles-seguras-juarez-api-i2sn.onrender.com/docs](https://calles-seguras-juarez-api-i2sn.onrender.com/docs)

---

## 1. Matriz de Cumplimiento de Requisitos

| Criterio / Entregable | Estado | Evidencia Técnica |
| :--- | :--- | :--- |
| **Arquitectura Full-Stack Desacoplada** | Cumplido | Frontend SPA en React + TypeScript + Vite (Vercel) conectado vía REST (`/api/v1`) a FastAPI (Render) y PostgreSQL (Neon). |
| **Base de Datos y Datos Realistas** | Cumplido | Esquema relacional en PostgreSQL poblado mediante `db/seed.py` con 4 sectores, 24 colonias reales de Ciudad Juárez y 500 reportes distribuidos en 12 semanas. |
| **Autenticación y Control de Roles (RBAC)** | Cumplido | Autenticación basada en JWT con permisos diferenciados para `ciudadano`, `moderador`, `coordinador` y `enlace` municipal. |
| **Privacidad y Anonimización (LFPDPPP)** | Cumplido | Las vistas y endpoints públicos omiten nombres, correos y datos personales de los ciudadanos reportantes. |
| **Enrutamiento SPA y Diseño Responsivo** | Cumplido | Configuración `frontend/vercel.json` para recarga limpia en rutas internas y diseño *mobile-first* validado en escritorio y móvil. |
| **Contenerización y Reproducibilidad** | Cumplido | Configuración `docker-compose.yml` y `Dockerfile` documentados en `README.md` para levantamiento local reproducible. |
| **Documentación y Gobernanza de IA** | Cumplido | Inclusión de `README.md`, `GEMINI.md`, `AI_USAGE.md`, `docs/AUTOEVALUACION.md` y `docs/REPORTE.pdf`. |

---

## 2. Evaluación Individual por Integrante

| Integrante | Responsabilidades Principales | Aportación (%) |
| :--- | :--- | :--- |
| **Omar Padilla Torres** | Arquitectura backend en FastAPI, modelado SQLAlchemy, script `db/seed.py`, despliegue en la nube (Neon, Render y Vercel), configuración CORS/SPA y documentación técnica. | 50% |
| **Daniel Valadez Macías** | Desarrollo de componentes frontend en React/TypeScript, integración de vistas analíticas/mapas, pruebas de flujo por roles y validación de interfaz responsiva. | 50% |

---

## 3. Lecciones Aprendidas y Mejoras Futuras

* **Gestión de entornos en producción:** La separación entre variables en tiempo de compilación (`VITE_API_URL` en Vite) y variables en tiempo de ejecución (`DATABASE_URL` y `CORS_ORIGINS` en FastAPI) resultó clave para estabilizar la comunicación entre Vercel y Render.
* **Siguientes pasos técnicos:** Incorporar almacenamiento en la nube para evidencia fotográfica adjunta en los reportes, notificaciones por correo al cambiar el estatus de un folio y pruebas automatizadas de extremo a extremo (E2E) en el pipeline de CI/CD.