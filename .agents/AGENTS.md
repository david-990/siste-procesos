# AGENTS.md — Flask/Python (siste-procesos)

## MCP — Codebase Memory

El proyecto puede estar indexado en `codebase-memory-mcp`.
SI las herramientas MCP de grafo están disponibles en la sesión, utilízalas preferentemente para:
- Buscar funciones: `search_graph` con `query='nombreFuncion'`
- Trazar callers: `trace_path` con `function_name='X', direction='inbound'`
- Ver arquitectura: `get_architecture`
- Buscar código completo: `search_code` con `mode='full'`

SI el proyecto no está indexado (o el grafo está desactualizado):
- Si la herramienta MCP `index_repository` está disponible en la sesión, ejecútala con `repo_path` (ej. `.` o la ruta absoluta) y `"persistence": true`.
- Si no está disponible en la sesión, ejecuta o sugiere la indexación vía CLI con: `codebase-memory-mcp cli index_repository '{"repo_path": "c:/Users/HP/Desktop/PROYECTOS/flask", "persistence": true}'` (usar la ruta absoluta del repositorio para evitar problemas de path).

SI las herramientas MCP NO están declaradas, fallan, o devuelven resultados insuficientes, usa inmediatamente las herramientas de búsqueda manuales (grep_search, list_dir, view_file) para evitar bloqueos.

## Ponytail skill

CARGAR al inicio de cualquier tarea de código:
- Usar `skill` tool con `name='ponytail'`
- Nivel: **full** por defecto
- Regla: mínimo diff, máximo impacto
- Comentarios descriptivos en español, NO traducir términos técnicos

# Ponytail, lazy senior dev mode

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here, don't re-write it.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

The ladder runs after you understand the problem, not instead of it: read the task and the code it touches, trace the real flow end to end, then climb.

Bug fix = root cause, not symptom: a report names a symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the path the ticket names leaves a sibling caller still broken.

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins, but only once you understand the problem. The smallest change in the wrong place is not a fix.
- Never cut validation, error handling, security, or accessibility.

## Componentes y Macros Reutilizables

ANTES de escribir UI nueva o añadir elementos HTML a las plantillas, VERIFICAR si ya existe una macro o plantilla en `app/templates/components.html`.
Si no existe lo que necesitas y se va a repetir en varias vistas, créalo como una macro allí y úsala.

**Macros en `app/templates/components.html`**:
- `page_header(title, subtitle)` — Cabecera de página con título y subtítulo (con estilos Tailwind CSS).
- `panel()` — Contenedor con borde, fondo blanco, padding y sombra. Se usa con `{% call panel() %} ... {% endcall %}`.
- `input(name, label, value='', type='text', width='', min=none, max=none)` — Campo de entrada con label y estilos de focus, deshabilitado e inválido.
- `select(name, label, options, selected=None, key='id', text='nombre', width='')` — Menú desplegable dinámico para opciones clave-valor.
- `button(label='Guardar')` — Botón con estilos principales del sistema de diseño (marca).
- `icon(name, class='h-5 w-5')` — Macro para renderizar iconos SVG inline predefinidos (`logo`, `panel`, `indicadores`, `acciones`, `procesos`, `mapa`, `lineas_base`, `metas_valores`, `metas_anuales`, `resumen`, `avances`, `settings`, `check`, `save`, `trash`, `edit`).

**Plantillas base**:
- `base.html` — Layout global del panel de administración (inyección de Tailwind CDN, SweetAlert2, Alpine.js y barra de navegación lateral sidebar).
- `empty_state.html` — Plantilla para mostrar estados vacíos con un mensaje personalizado.

Reglas:
- NUNCA dupliques clases HTML de Tailwind para inputs, botones, tablas o cabeceras si ya existe una macro.
- Las vistas extienden de `base.html` e implementan el contenido principal dentro de `{% block content %}`.

## Non-discoverable commands

- Servidor de desarrollo: `python run.py` (corre en `http://127.0.0.1:5000` con debug activo)
- Pruebas automatizadas: `pytest`
- Producción local/Staging (Gunicorn): `gunicorn run:app --bind 0.0.0.0:$PORT`

## Landmines (Minas / Puntos de Cuidado)

- **CSRF Protection**: Todas las peticiones `POST` de formularios deben incluir obligatoriamente el campo `<input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">` o el token de sesión. Su ausencia causa error 400 Bad Request.
- **Conversión de decimales**: Para obtener floats desde formularios, usar el método helper `_float_value(name)` de `app/routes.py` para reemplazar comas `,` por puntos `.` y prevenir fallos en la conversión.
- **Vulnerabilidad de Open Redirect**: Al redireccionar post-login, procesar la URL con `_safe_next_url(value)` para validar que sea una ruta interna segura.
- **Base de datos MySQL**: Conexión manual por request mediante `get_connection()` en `app/db.py`. Evitar fugas de conexiones y parameterizar siempre las consultas SQL para prevenir inyección SQL.

## Architecture

- `run.py` — Punto de entrada para el servidor Flask local.
- `requirements.txt` — Dependencias del proyecto Python (Flask, gunicorn, mysql-connector-python, pytest, python-dotenv).
- `schema.sql` — Estructura del esquema de base de datos MySQL.
- `app/__init__.py` — Factory pattern de Flask (`create_app`), registro de blueprints y manejadores de errores de base de datos.
- `app/config.py` — Lectura de variables de entorno del archivo `.env` y configuración de conexión MySQL (`DB_CONFIG`).
- `app/db.py` — Context manager y helpers de consulta a la base de datos (`fetch_all`, `fetch_one`, `execute`, `execute_many`).
- `app/repositories.py` — Capa de persistencia con consultas SQL puras parametrizadas para usuarios, gestiones, periodos, indicadores, acciones, etc.
- `app/routes.py` — Lógica de controladores y enrutamiento Flask. Contiene filtros globales (`before_app_request`) y la lógica de negocio de los endpoints.
- `app/services.py` / `app/reporte_ceplan_service.py` — Servicios auxiliares para la lógica de cálculo y reportes complejos.
- `app/templates/` — Vistas HTML procesadas mediante Jinja.
- `tests/` — Pruebas unitarias y de integración que usan `pytest` y mocks de repositorios.

## Agregar una nueva funcionalidad/módulo

1. Si requiere cambios en la base de datos, documentar en `schema.sql`.
2. Agregar métodos de consulta en `app/repositories.py` utilizando los helpers de `app/db.py`.
3. Definir la lógica de la ruta en `app/routes.py`.
4. Para restringir rutas de administrador, agregar su nombre de endpoint a `ADMIN_ENDPOINTS` en `app/routes.py`. Si requiere acceso público, agregar a `PUBLIC_ENDPOINTS`.
5. Crear o modificar la plantilla correspondiente en `app/templates/` heredando de `base.html` e importando macros de `components.html` para mantener coherencia visual.
6. Agregar las opciones correspondientes a la navegación lateral en el array de `sections` en `app/templates/base.html` si es necesario mostrar el enlace en el sidebar.
7. Añadir pruebas en `tests/` para verificar el correcto funcionamiento.

## Auth flow

- **Login**: Petición `POST /login` → valida credenciales del usuario con `check_password_hash` contra el hash almacenado en base de datos.
- **Sesión**: Si es correcto, establece `session["user_id"] = user['id']`.
- **Filtro global**: El hook `before_app_request` de Flask valida la existencia de la sesión para todas las rutas que no estén en `PUBLIC_ENDPOINTS`.
- **Roles**: En el hook de enrutamiento, si el endpoint de destino está listado en `ADMIN_ENDPOINTS`, verifica que `g.current_user["role"] == "ADMIN"`, de lo contrario lanza `abort(403)`.
- **Logout**: Limpia la sesión y redirige al usuario a `/login`.
