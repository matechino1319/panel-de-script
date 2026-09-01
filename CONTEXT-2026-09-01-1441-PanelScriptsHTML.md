# Contexto del proyecto

## Última actualización
2026-09-01 14:41

## Estado actual
Portal web integral del Departamento de Informática de LA YUNTA con panel de scripts automáticos, repositorio dinámico de herramientas descargables, catálogo dinámico de aplicaciones web y administración de usuarios. Cuenta con autenticación centralizada contra Supabase/PostgreSQL, almacenamiento de código y descargas en la nube, y gestión completa mediante menús de tres puntos (`⋮`) para editar y eliminar scripts, descargas y aplicaciones web.

## Decisiones técnicas
- **Gestión Dinámica de Aplicaciones Web (`index.html` / `app.py` / `db.py`)**: Tabla `portal_apps` en base de datos para registrar enlaces a plataformas internas/externas con icono seleccionable, badge personalizado y acciones CRUD mediante menú de tres puntos (`⋮`).
- **Almacenamiento Directo en Supabase Storage & PostgreSQL**: Subida de archivos desde el navegador directamente al bucket `descargas` de Supabase Storage mediante la API anónima, evitando el límite de 4.5 MB de Vercel Serverless.
- **Soporte Dual en Descargas (`descargas.html`)**: Pestaña para subida directa de archivos locales (<50 MB) y pestaña para enlaces externos (Google Drive / OneDrive / Mega) para paquetes pesados.
- **Acciones CRUD con Menú de Tres Puntos (`⋮`)**: Menús contextuales en tarjetas de scripts dinámicos, descargas y aplicaciones web para edición y borrado en base de datos sin recargar la página.
- **Conector Resiliente a Base de Datos (`db.py`)**: Parseo granular de `DATABASE_URL` para aceptar contraseñas con caracteres especiales sin fallas de percent-encoding, auto-creación de tablas (`usuarios`, `custom_scripts`, `descargas`, `portal_apps`) y políticas de Storage RLS.
- **Gestión de Seguridad Restringida (`auth.js` / `login.html`)**: La creación y cambio de contraseñas de usuarios administradores se encuentra disponible únicamente dentro de la sesión autenticada.

## Problemas conocidos
- Ninguno activo. Límite de Supabase Storage en plan gratuito fijado en 50 MB por archivo (mitigado con la pestaña de enlaces externos).

## Próximos pasos
- Continuar agregando scripts operativos al catálogo según requerimientos del equipo.
- Monitorear el uso del almacenamiento en Supabase Storage.

---

## Historial de sesiones

### Sesión 2026-09-01

**Completado:**
- Módulo de Aplicaciones Web dinámicas en la página de inicio (`index.html`).
- Persistencia de aplicaciones web en tabla `portal_apps` con sembrado de herramientas predeterminadas.
- Endpoints REST `GET /api/apps`, `POST /api/apps`, `PUT /api/apps/<id>` y `DELETE /api/apps/<id>` con fallback en memoria.
- Modales para agregar y editar aplicaciones web con selector de íconos, badges y enlaces.
- Menús de tres puntos (`⋮`) para edición y borrado en tiempo real de aplicaciones web y scripts dinámicos.
- Resiliencia de conexión a PostgreSQL/Supabase ante contraseñas complejas.
- Centralización de la creación y cambio de contraseñas en el dashboard (`auth.js`).
- Módulo de descargas con subida directa a Supabase Storage y enlaces externos.

**Modificado:**
- `app.py` — Endpoints CRUD para aplicaciones web (`/api/apps`), scripts (`/api/scripts/<id>`), descargas (`/api/descargas/<id>`), y cambio de clave (`/api/cambiar-password`).
- `db.py` — Tablas `portal_apps`, `custom_scripts` y `descargas`, funciones de actualización/eliminación y auto-configuración de políticas RLS.
- `index.html` — Carga asíncrona de aplicaciones web, modales de gestión y menú de tres puntos contextual.
- `descargas.html` — Modal con pestañas (Subida Supabase / Enlace externo), menú de tres puntos, modal de edición y eliminación reactiva.
- `scripts.html` — Modal de edición de scripts personalizados y alertas unificadas.
- `script.js` — Menú de tres puntos en tarjetas dinámicas, integración con endpoints `PUT`/`DELETE`.
- `auth.js` — Modales de creación de usuarios y cambio de contraseña dentro del navbar.
- `style.css` — Estilos para menú desplegable de tres puntos (`.card-actions-menu`, `.card-dropdown`).

**Pendiente:**
- Ninguno en esta fase.

### Sesión 2026-08-27

**Completado:**
- Creación de la página de inicio de sesión (`login.html`) adaptada a la estética blanco y rojo de LA YUNTA.
- Implementación del módulo de autenticación en cliente (`auth.js`) y widget de usuario en la cabecera.
- Generación de estilos de login, inputs, tarjetas y controles de sesión en `style.css`.
- Creación del esquema SQL para login con rol de administrador único (`schema.sql`).
- Implementación de `db.py` con soporte para PostgreSQL, MySQL y fallback a SQLite local.
- Creación del endpoint `POST /api/login` en `app.py`.
- Integración de drivers de base de datos (`psycopg2-binary`, `PyMySQL`) en `requirements.txt`.
- Commits y pushes a GitHub en rama `main`.

**Modificado:**
- `login.html` (NUEVO) — Pantalla de login de sesión con formulario interactivo y feedback de errores.
- `auth.js` (NUEVO) — Control de estado de sesión, redirecciones y widget en barra de navegación.
- `db.py` (NUEVO) — Conector multi-motor para PostgreSQL, MySQL y SQLite local con auto-creación de tablas y validación de hash.
- `schema.sql` (NUEVO) — Script DDL/DML para tabla `usuarios` y seed del usuario admin.
- `app.py` — Integración del endpoint `/api/login` y carga de DB.
- `requirements.txt` — Incorporación de drivers `psycopg2-binary` y `PyMySQL`.
- `style.css` — Estilos de login, inputs con iconos, animaciones y widget de sesión.
- `index.html`, `scripts.html`, `descargas.html` — Inclusión del guardián `auth.js` y controles de sesión.

**Pendiente:**
- Carga de `DATABASE_URL` en Vercel Dashboard si se desea persistencia remota en la nube.

### Sesión 2026-08-25

**Completado:**
- Eliminación de la imagen de fondo en todas las vistas.
- Reestructuración de la página de inicio con diseño moderno en blanco y rojo.
- Actualización de estilos, tarjetas, estados interactivos y dropzones en `style.css`.
- Estandarización de cabeceras y navegación en `index.html`, `scripts.html` y `descargas.html`.
- Actualización del favicon a gradiente rojo institucional.
- Incorporación de iconos dedicados en `script.js` para nuevos scripts.
- Push exitoso a la rama `main` de GitHub.

**Modificado:**
- `style.css` — Sistema de diseño blanco y rojo corporativo, eliminación de fondos con imagen y nuevos estilos de tarjetas.
- `index.html` — Estructura limpia y semántica con grilla de accesos rápidos.
- `descargas.html` — Ajuste de fondo, cabecera y catálogo descargable.
- `scripts.html` — Cabecera unificada y corrección estética.
- `script.js` — Mapeo de iconos para herramientas de promociones y fondo de imagen.
- `favicon.svg` — Icono con gradiente rojo.

**Pendiente:**
- Ninguno en esta fase.

### Sesión 2026-08-24

**Completado:**
- Rediseño completo de la página inicial (`index.html`) para adaptarla a la identidad visual de Informática LA YUNTA.
- Incorporación de logo de alta resolución como imagen de fondo en toda la pantalla.
- Cambio de nombre y diseño de icono para "Retail Monitor".
- Creación de apartado dedicado a descargas (`descargas.html`).
- Subida y configuración del "Analizador de Particiones" (.zip) listo para descarga.

**Modificado:**
- `index.html` — Rediseño completo: eliminación de barra superior, nuevo grid de opciones, enlaces actualizados, estilos glassmorphism integrados, y cambio de ícono/nombre de Retail Monto.
- `style.css` — Cambio general de tema (colores primarios, brillos y gradientes pasaron de azul a rojo/negro).
- `descargas.html` (NUEVO) — Página con estructura similar a index para agrupar herramientas descargables.
- `logo_la_yunta_highres.png` (NUEVO) — Logo principal.
- `analizador_particiones.zip` (NUEVO) — Archivo listo para ser descargado.

**Pendiente:**
- Ninguno en esta fase.
