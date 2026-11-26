# AI_USAGE.md — Registro de Uso Responsable de Inteligencia Artificial

## 1. Propósito y Alcance
Este documento transparenta el uso de herramientas de Inteligencia Artificial Generativa durante el diseño, desarrollo, pruebas y despliegue del proyecto **Calles Seguras Juárez**, asegurando la trazabilidad, autoría humana y validación técnica de cada componente entregado.

---

## 2. Herramientas Empleadas

* **Google Gemini:** Asistencia en arquitectura de software, estructuración de modelos de datos, revisión de configuración de despliegue en la nube (Vercel, Render y Neon), depuración de errores de CORS/SPA y redacción de documentación técnica.
* **Asistentes de autocompletado en IDE (VS Code):** Apoyo en sintaxis repetitiva de TypeScript, esquemas Pydantic y consultas SQLAlchemy.

---

## 3. Bitácora de Actividades Asistidas por IA

| Fase del Proyecto | Tarea Asistida | Intervención y Validación Humana |
| :--- | :--- | :--- |
| **Diseño y Datos (`db/seed.py`)** | Generación de estructura inicial para poblar 4 sectores, 24 colonias y 500 reportes históricos distribuidos en 12 semanas. | Selección y verificación de nombres reales de colonias y coordenadas geográficas de **Ciudad Juárez, Chihuahua**; ajuste de distribución estadística por categoría de incidencia. |
| **Backend (`FastAPI`)** | Revisión de endpoints REST bajo `/api/v1`, validación de esquemas Pydantic v2 y políticas de control de acceso basado en roles (RBAC). | Implementación de seguridad JWT, ajuste de zona horaria oficial (`America/Ciudad_Juarez`) y anonimización de datos personales conforme a la **LFPDPPP**. |
| **Frontend (`React + Vite`)** | Diagnóstico de enrutamiento SPA y manejo de variables de entorno públicas (`VITE_API_URL`) en tiempo de compilación. | Pruebas manuales de interfaz responsiva (*mobile-first*), verificación de flujos de inicio de sesión para los 5 roles y validación visual en producción. |
| **Despliegue Cloud (PaaS / DBaaS)** | Resolución de políticas `CORS_ORIGINS` entre Vercel y Render, y reglas de reescritura en `frontend/vercel.json` (UTF-8 sin BOM). | Configuración directa de secretos y variables en paneles de Neon, Render y Vercel; pruebas de persistencia de lectura y escritura en base de datos remota. |
| **Documentación (`README.md`, `GEMINI.md`)** | Estructuración de guías de instalación, tabla de credenciales de prueba y contexto técnico del repositorio. | Auditoría de enlaces públicos, comandos de ejecución en Windows/Docker y verificación de cumplimiento con la rúbrica de entrega. |

---

## 4. Criterios de Verificación y Gobernanza

1. **Cero código a ciegas:** Ningún fragmento sugerido por IA fue integrado sin lectura previa, pruebas locales (`localhost`) y validación en el entorno de producción.
2. **Protección de credenciales:** Las llaves secretas (`SECRET_KEY`, `DATABASE_URL` de Neon) fueron gestionadas exclusivamente de forma manual mediante variables de entorno cifradas en Render y jamás fueron expuestas en prompts ni en el repositorio Git.
3. **Autoría:** La arquitectura funcional, toma de decisiones de ingeniería, integración de módulos y pruebas finales fueron ejecutadas y aprobadas por **Omar Padilla Torres** y **Daniel Valadez Macías** (Instituto Tecnológico de Ciudad Juárez).