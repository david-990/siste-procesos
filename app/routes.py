import os
import time
from calendar import monthrange
from datetime import date
from secrets import token_urlsafe
from time import monotonic

from flask import Blueprint, abort, flash, g, redirect, render_template, request, send_file, session, url_for
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

from app import repositories as repo
from app import services
from app import reporte_ceplan_service
from app import ai_service
from app import storage


bp = Blueprint("main", __name__)
PUBLIC_ENDPOINTS = {"main.login", "static", "main.logo_ia"}
ADMIN_ENDPOINTS = {
    "main.objetivos",
    "main.objetivo_eliminar",
    "main.acciones",
    "main.accion_eliminar",
    "main.metas_anuales",
    "main.meta_anual_eliminar",
    "main.indicadores",
    "main.indicador_estado",
    "main.indicador_eliminar",
    "main.vinculacion",
    "main.vinculacion_eliminar",
    "main.lineas_base",
    "main.linea_base_eliminar",
    "main.metas_valores",
    "main.procesos",
    "main.proceso_eliminar",
    "main.mapa",
}
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW_SECONDS = 300
_LOGIN_ATTEMPTS = {}


def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(name):
    value = request.form.get(name, "").strip().replace(",", ".")
    try:
        return float(value) if value else None
    except ValueError:
        return None


def _optional_value(name):
    value = request.form.get(name, "").strip()
    return value or None


def _estado_avance(avance):
    if avance is None:
        return {
            "nombre": "Sin dato",
            "clase": "bg-slate-100 text-slate-600 border-slate-200",
            "barra": "bg-slate-300",
        }
    if avance < 75:
        return {
            "nombre": "Critico",
            "clase": "bg-red-100 text-red-700 border-red-200",
            "barra": "bg-red-500",
        }
    if avance < 95:
        return {
            "nombre": "En seguimiento",
            "clase": "bg-amber-100 text-amber-700 border-amber-200",
            "barra": "bg-amber-400",
        }
    return {
        "nombre": "Concluido",
        "clase": "bg-emerald-100 text-emerald-700 border-emerald-200",
        "barra": "bg-emerald-500",
    }


def _alerta_cierre(gestion_nombre, mes_fin):
    anio = int(gestion_nombre)
    ultimo_dia = monthrange(anio, int(mes_fin))[1]
    cierre = date(anio, int(mes_fin), ultimo_dia)
    dias = (cierre - date.today()).days
    if dias > 0:
        texto = f"Faltan {dias} días para el cierre"
        clase = "bg-blue-50 text-blue-700 border-blue-200"
    elif dias == 0:
        texto = "El periodo cierra hoy"
        clase = "bg-amber-50 text-amber-700 border-amber-200"
    else:
        texto = f"Cerrado hace {abs(dias)} días"
        clase = "bg-slate-100 text-slate-600 border-slate-200"
    return {"dias": dias, "fecha": cierre, "texto": texto, "clase": clase}


def _alerta_por_estado(estado, gestion_nombre, mes_fin):
    if estado["nombre"] == "Concluido":
        return {
            "dias": None,
            "fecha": None,
            "texto": "Indicador concluido",
            "clase": "bg-emerald-50 text-emerald-700 border-emerald-200",
        }
    return _alerta_cierre(gestion_nombre, mes_fin)


def _csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@bp.app_context_processor
def inject_globals():
    return {"csrf_token": _csrf_token, "current_user": getattr(g, "current_user", None)}


@bp.before_app_request
def protect_requests():
    if request.endpoint is None:
        return None
    if request.method == "POST":
        csrf_val = None
        if request.is_json:
            csrf_val = request.headers.get("X-CSRFToken") or request.json.get("_csrf_token")
        else:
            csrf_val = request.form.get("_csrf_token")
        if not csrf_val or csrf_val != session.get("_csrf_token"):
            abort(400)
    if request.endpoint not in PUBLIC_ENDPOINTS and not session.get("user_id"):
        return redirect(url_for("main.login", next=request.full_path))
    try:
        g.current_user = repo.get_user_by_id(session["user_id"]) if session.get("user_id") else None
    except mysql.connector.Error:
        g.current_user = None
    if request.endpoint in ADMIN_ENDPOINTS and (not g.current_user or g.current_user["role"] != "ADMIN"):
        abort(403)
    if request.endpoint == "main.avances" and request.method == "POST" and g.current_user["role"] != "ADMIN":
        abort(403)


def _require_data(*collections):
    return all(collections)


def _empty_state(message):
    flash(message)
    return render_template("empty_state.html", message=message)


def _safe_next_url(value):
    return value if value and value.startswith("/") and not value.startswith("//") else url_for("main.panel")


def _login_key(username):
    return f"{request.remote_addr or 'local'}:{username.lower()}"


def _login_rate_limited(username):
    attempts = [
        attempt
        for attempt in _LOGIN_ATTEMPTS.get(_login_key(username), [])
        if monotonic() - attempt < LOGIN_ATTEMPT_WINDOW_SECONDS
    ]
    _LOGIN_ATTEMPTS[_login_key(username)] = attempts
    return len(attempts) >= LOGIN_ATTEMPT_LIMIT


def _record_failed_login(username):
    key = _login_key(username)
    _LOGIN_ATTEMPTS.setdefault(key, []).append(monotonic())


def _clear_login_attempts(username):
    _LOGIN_ATTEMPTS.pop(_login_key(username), None)


@bp.route("/logo-ia")
def logo_ia():
    logo_path = os.path.join(os.path.dirname(__file__), "logotipo-ia.png")
    return send_file(logo_path, mimetype="image/png")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.panel"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if _login_rate_limited(username):
            flash("Demasiados intentos. Inténtalo nuevamente en unos minutos.")
            return render_template("login.html"), 429
        user = repo.get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["_csrf_token"] = token_urlsafe(32)
            _clear_login_attempts(username)
            return redirect(_safe_next_url(request.args.get("next")))
        _record_failed_login(username)
        flash("Usuario o clave incorrectos.")

    return render_template("login.html")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/password", methods=["GET", "POST"])
def change_password():
    user = g.current_user
    if not user:
        session.clear()
        return redirect(url_for("main.login"))
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        db_user = repo.get_user_by_username(user["username"])

        if not db_user or not check_password_hash(db_user["password_hash"], current_password):
            flash("La clave actual no es correcta.")
        elif len(new_password) < 8:
            flash("La nueva clave debe tener al menos 8 caracteres.")
        elif new_password != confirm_password:
            flash("La confirmación de clave no coincide.")
        else:
            repo.update_user_password(user["id"], generate_password_hash(new_password))
            flash("Clave actualizada.")
            return redirect(url_for("main.panel"))

    return render_template("password.html")


@bp.route("/")
def index():
    return redirect(url_for("main.panel"))


@bp.route("/panel")
def panel():
    gestiones = repo.get_gestiones()
    if not _require_data(gestiones):
        return _empty_state("No hay gestiones registradas.")
    gestion_id = _safe_int(request.args.get("gestion_id"), repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    if not _require_data(periodos):
        return _empty_state("No hay periodos registrados para la gestión seleccionada.")
    periodo_id = _safe_int(request.args.get("periodo_id"), periodos[0]["id"])
    periodo = next((p for p in periodos if p["id"] == periodo_id), periodos[0])
    gestion = next((g for g in gestiones if g["id"] == gestion_id), gestiones[0])
    seguimiento = repo.get_panel_seguimiento(gestion_id, periodo_id)
    evolucion = repo.get_panel_evolucion(gestion_id, periodo_id)
    alerta_cierre = _alerta_cierre(gestion["nombre"], periodo["mes_fin"])

    for fila in seguimiento:
        avance = float(fila["avance_tipo_1"]) if fila["avance_tipo_1"] is not None else None
        fila["estado"] = _estado_avance(avance)
        fila["alerta"] = _alerta_por_estado(fila["estado"], gestion["nombre"], periodo["mes_fin"])
        fila["avance_tipo_1_vista"] = services.limitar_porcentaje(avance)

    total_indicadores = len(seguimiento)
    resultados = [float(f["avance_tipo_1"]) for f in seguimiento if f["avance_tipo_1"] is not None]

    avances_acciones_db = repo.fetch_all(
        """
        SELECT aa.resultado
        FROM avances_acciones_estrategicas aa
        JOIN periodos p ON aa.periodo_id = p.id
        WHERE p.id = %s AND p.gestion_id = %s AND aa.tipo_avance = 'TIPO_1'
        """,
        (periodo_id, gestion_id)
    )
    avance_acciones_promedio = sum(float(r["resultado"]) for r in avances_acciones_db) / len(avances_acciones_db) if avances_acciones_db else None

    avances_objetivos_db = repo.fetch_all(
        """
        SELECT ao.resultado
        FROM avances_objetivos_estrategicos ao
        JOIN periodos p ON ao.periodo_id = p.id
        WHERE p.id = %s AND p.gestion_id = %s AND ao.tipo_avance = 'TIPO_1'
        """,
        (periodo_id, gestion_id)
    )
    avance_objetivos_promedio = sum(float(r["resultado"]) for r in avances_objetivos_db) / len(avances_objetivos_db) if avances_objetivos_db else None

    conteo_estados = {"Critico": 0, "En seguimiento": 0, "Concluido": 0, "Sin dato": 0}
    for fila in seguimiento:
        conteo_estados[fila["estado"]["nombre"]] += 1

    # Obtener el resumen ejecutivo de IA si ya existe en la base de datos
    ai_resumen = repo.get_resumen_ia(gestion_id, periodo_id)
    ai_kurt_lewin = repo.get_kurt_lewin_ia(gestion_id, periodo_id)

    return render_template(
        "panel.html",
        gestiones=gestiones,
        periodos=periodos,
        gestion_id=gestion_id,
        periodo_id=periodo_id,
        periodo=periodo,
        alerta_cierre=alerta_cierre,
        total_indicadores=total_indicadores,
        evaluados=len(resultados),
        avance_acciones_promedio=avance_acciones_promedio,
        avance_objetivos_promedio=avance_objetivos_promedio,
        seguimiento=seguimiento,
        bar_labels=[f["codigo"] for f in seguimiento if f["avance_tipo_1"] is not None],
        bar_values=[round(services.limitar_porcentaje(f["avance_tipo_1"]), 2) for f in seguimiento if f["avance_tipo_1"] is not None],
        line_labels=[f["mes"] for f in evolucion],
        line_meta_values=[float(f["meta_promedio"]) if f["meta_promedio"] is not None else None for f in evolucion],
        line_meta_anual_values=[float(f["meta_anual_promedio"]) if f["meta_anual_promedio"] is not None else None for f in evolucion],
        line_valor_values=[float(f["valor_promedio"]) if f["valor_promedio"] is not None else None for f in evolucion],
        donut_values=[
            conteo_estados["Concluido"],
            conteo_estados["En seguimiento"],
            conteo_estados["Critico"],
            conteo_estados["Sin dato"],
        ],
        ai_resumen=ai_resumen,
        ai_kurt_lewin=ai_kurt_lewin,
    )


@bp.post("/panel/generar-resumen")
def panel_generar_resumen():
    gestion_id = _safe_int(request.form.get("gestion_id"))
    periodo_id = _safe_int(request.form.get("periodo_id"))
    
    gestiones = repo.get_gestiones()
    gestion = next((g for g in gestiones if g["id"] == gestion_id), None)
    periodos = repo.get_periodos(gestion_id) if gestion_id else []
    periodo = next((p for p in periodos if p["id"] == periodo_id), None)

    if not gestion or not periodo:
        flash("Datos de gestión o periodo inválidos.")
        return redirect(url_for("main.panel", gestion_id=gestion_id, periodo_id=periodo_id))

    seguimiento = repo.get_panel_seguimiento(gestion_id, periodo_id)
    
    # Calcular métricas para el prompt
    for fila in seguimiento:
        avance = float(fila["avance_tipo_1"]) if fila["avance_tipo_1"] is not None else None
        fila["estado"] = _estado_avance(avance)

    total_indicadores = len(seguimiento)
    resultados = [float(f["avance_tipo_1"]) for f in seguimiento if f["avance_tipo_1"] is not None]

    avances_acciones_db = repo.fetch_all(
        """
        SELECT aa.resultado
        FROM avances_acciones_estrategicas aa
        JOIN periodos p ON aa.periodo_id = p.id
        WHERE p.id = %s AND p.gestion_id = %s AND aa.tipo_avance = 'TIPO_1'
        """,
        (periodo_id, gestion_id)
    )
    avance_acciones_promedio = sum(float(r["resultado"]) for r in avances_acciones_db) / len(avances_acciones_db) if avances_acciones_db else None

    avances_objetivos_db = repo.fetch_all(
        """
        SELECT ao.resultado
        FROM avances_objetivos_estrategicos ao
        JOIN periodos p ON ao.periodo_id = p.id
        WHERE p.id = %s AND p.gestion_id = %s AND ao.tipo_avance = 'TIPO_1'
        """,
        (periodo_id, gestion_id)
    )
    avance_objetivos_promedio = sum(float(r["resultado"]) for r in avances_objetivos_db) / len(avances_objetivos_db) if avances_objetivos_db else None

    conteo_estados = {"Critico": 0, "En seguimiento": 0, "Concluido": 0, "Sin dato": 0}
    for fila in seguimiento:
        conteo_estados[fila["estado"]["nombre"]] += 1

    # Llamar al servicio de IA
    resumen = ai_service.generar_resumen_panel(
        gestion_nombre=gestion["nombre"],
        periodo_nombre=periodo["nombre"],
        total_indicadores=total_indicadores,
        evaluados=len(resultados),
        avance_acciones=avance_acciones_promedio,
        avance_objetivos=avance_objetivos_promedio,
        conteo_estados=conteo_estados,
        seguimiento=seguimiento
    )

    # Guardar en base de datos
    repo.save_resumen_ia(gestion_id, periodo_id, resumen)
    flash("Resumen ejecutivo generado con IA con éxito.")
    
    return redirect(url_for("main.panel", gestion_id=gestion_id, periodo_id=periodo_id))


@bp.post("/panel/generar-kurt-lewin")
def panel_generar_kurt_lewin():
    gestion_id = _safe_int(request.form.get("gestion_id"))
    periodo_id = _safe_int(request.form.get("periodo_id"))

    gestiones = repo.get_gestiones()
    gestion = next((g for g in gestiones if g["id"] == gestion_id), None)
    periodos = repo.get_periodos(gestion_id) if gestion_id else []
    periodo = next((p for p in periodos if p["id"] == periodo_id), None)

    if not gestion or not periodo:
        flash("Datos de gestión o periodo inválidos.")
        return redirect(url_for("main.panel", gestion_id=gestion_id, periodo_id=periodo_id))

    seguimiento = repo.get_panel_seguimiento(gestion_id, periodo_id)
    for fila in seguimiento:
        avance = float(fila["avance_tipo_1"]) if fila["avance_tipo_1"] is not None else None
        fila["estado"] = _estado_avance(avance)

    kurt_lewin = ai_service.generar_kurt_lewin_panel(
        gestion_nombre=gestion["nombre"],
        periodo_nombre=periodo["nombre"],
        seguimiento=seguimiento,
    )

    repo.save_kurt_lewin_ia(gestion_id, periodo_id, kurt_lewin)
    flash("Implementación del modelo de Kurt Lewin generada con IA con éxito.")

    return redirect(url_for("main.panel", gestion_id=gestion_id, periodo_id=periodo_id))


@bp.get("/panel/analisis/<tipo>/pdf")
def panel_analisis_pdf(tipo):
    gestion_id = _safe_int(request.args.get("gestion_id"), repo.get_default_gestion_id())
    periodo_id = _safe_int(request.args.get("periodo_id"))
    gestiones = repo.get_gestiones()
    gestion = next((g for g in gestiones if g["id"] == gestion_id), None)
    periodos = repo.get_periodos(gestion_id) if gestion_id else []
    periodo = next((p for p in periodos if p["id"] == periodo_id), None)

    if not gestion or not periodo:
        flash("Datos de gestión o periodo inválidos.")
        return redirect(url_for("main.panel", gestion_id=gestion_id, periodo_id=periodo_id))

    reports = {
        "resumen": ("Resumen Ejecutivo con IA", repo.get_resumen_ia(gestion_id, periodo_id)),
        "kurt-lewin": ("Implementación del Modelo de Kurt Lewin", repo.get_kurt_lewin_ia(gestion_id, periodo_id)),
    }
    if tipo not in reports:
        abort(404)

    title, content = reports[tipo]
    if not content:
        flash("Primero genera el análisis antes de exportarlo a PDF.")
        return redirect(url_for("main.panel", gestion_id=gestion_id, periodo_id=periodo_id))

    return render_template(
        "analisis_pdf.html",
        title=title,
        content=content,
        gestion=gestion,
        periodo=periodo,
    )


@bp.route("/objetivos", methods=["GET", "POST"])
def objetivos():
    if request.method == "POST":
        repo.save_objetivo(
            {
                "nombre": request.form["nombre"].strip(),
            },
            request.form.get("id") or None,
        )
        flash("Objetivo estratégico guardado.")
        return redirect(url_for("main.objetivos"))

    return render_template(
        "objetivos_estrategicos.html",
        objetivos=repo.get_objetivos(),
    )


@bp.post("/objetivos/<int:objetivo_id>/eliminar")
def objetivo_eliminar(objetivo_id):
    repo.delete_objetivo(objetivo_id)
    flash("Objetivo estratégico eliminado.")
    return redirect(url_for("main.objetivos"))


@bp.route("/procesos", methods=["GET", "POST"])
def procesos():
    if request.method == "POST":
        proceso_id = _safe_int(request.form.get("id")) or None
        nivel = _safe_int(request.form.get("nivel"))
        proceso_padre_id = _safe_int(request.form.get("proceso_padre_id")) or None
        tipo_proceso = request.form.get("tipo_proceso", "").strip()
        producto_proceso = request.form.get("producto_proceso", "").strip()
        codigo_proceso = request.form.get("codigo_proceso", "").strip()
        nombre_proceso = request.form.get("nombre_proceso", "").strip()

        errors = []
        if nivel is None or not (0 <= nivel <= 3):
            errors.append("El nivel del proceso debe estar entre 0 y 3.")
        
        # Validar relación de padre
        if nivel == 0:
            proceso_padre_id = None
        else:
            if not proceso_padre_id:
                errors.append("Para niveles mayores a 0, se debe seleccionar un proceso padre.")
            elif proceso_id and proceso_padre_id == proceso_id:
                errors.append("Un proceso no puede ser su propio padre.")
            else:
                padre = repo.get_proceso(proceso_padre_id)
                if not padre:
                    errors.append("El proceso padre seleccionado no existe.")
                elif padre["nivel"] != (nivel - 1):
                    errors.append(f"El proceso padre debe ser de Nivel {nivel - 1}.")
                else:
                    # Heredar el tipo de proceso del padre obligatoriamente
                    tipo_proceso = padre["tipo_proceso"]
                    
                    # Validar ciclos de dependencia (que el padre no sea un descendiente del proceso actual)
                    if proceso_id:
                        curr_id = proceso_padre_id
                        visited = set()
                        while curr_id:
                            if curr_id == proceso_id:
                                errors.append("No se puede seleccionar un proceso descendente como padre (ciclo de dependencia).")
                                break
                            if curr_id in visited:
                                break
                            visited.add(curr_id)
                            parent_row = repo.get_proceso(curr_id)
                            curr_id = parent_row["proceso_padre_id"] if parent_row else None

        # Si el proceso ya tiene hijos, validar que no se altere su nivel
        if proceso_id and not errors:
            original = repo.get_proceso(proceso_id)
            if original and original["nivel"] != nivel:
                has_children = repo.fetch_one("SELECT 1 FROM procesos WHERE proceso_padre_id = %s LIMIT 1", (proceso_id,))
                if has_children:
                    errors.append("No se puede cambiar el nivel de este proceso porque tiene subprocesos dependientes registrados.")

        if tipo_proceso not in ("Estratégico", "Misional", "Apoyo"):
            errors.append("Selecciona un tipo de proceso válido.")
        if not producto_proceso:
            errors.append("El producto del proceso es requerido.")
        if not codigo_proceso:
            errors.append("El código del proceso es requerido.")
        if not nombre_proceso:
            errors.append("El nombre del proceso es requerido.")

        # Verificar unicidad del codigo_proceso
        if codigo_proceso:
            existing = repo.get_proceso_by_codigo(codigo_proceso)
            if existing and (proceso_id is None or existing["id"] != proceso_id):
                errors.append(f"El código de proceso '{codigo_proceso}' ya está registrado.")

        if errors:
            for err in errors:
                flash(err)
        else:
            repo.save_proceso(
                {
                    "nivel": nivel,
                    "tipo_proceso": tipo_proceso,
                    "producto_proceso": producto_proceso,
                    "codigo_proceso": codigo_proceso,
                    "nombre_proceso": nombre_proceso,
                    "proceso_padre_id": proceso_padre_id,
                },
                proceso_id,
            )
            flash("Proceso guardado correctamente.")
            return redirect(url_for("main.procesos"))

    return render_template("procesos.html", procesos=repo.get_procesos())


@bp.post("/procesos/<int:proceso_id>/eliminar")
def proceso_eliminar(proceso_id):
    # Validar si tiene hijos antes de intentar eliminar
    has_children = repo.fetch_one("SELECT 1 FROM procesos WHERE proceso_padre_id = %s LIMIT 1", (proceso_id,))
    if has_children:
        flash("No se puede eliminar el proceso porque tiene subprocesos dependientes registrados. Elimínalos o reasígnalos primero.")
        return redirect(url_for("main.procesos"))
        
    repo.delete_proceso(proceso_id)
    flash("Proceso eliminado.")
    return redirect(url_for("main.procesos"))


@bp.route("/ficha-caracterizacion")
def fichas_caracterizacion():
    fichas = repo.get_fichas_caracterizacion()
    for f in fichas:
        if f.get("actividades_proceso_imagen"):
            f["imagen_signed_url"] = storage.get_signed_url(f["actividades_proceso_imagen"])
    return render_template("ficha_caracterizacion_list.html", fichas=fichas)


def _save_ficha_form(ficha=None):
    required_fields = [
        ("nombre_proceso", "El nombre del proceso es requerido."),
        ("codigo_proceso", "El código del proceso es requerido."),
        ("objetivo_proceso", "El objetivo del proceso es requerido."),
    ]
    errors = []
    for field_name, message in required_fields:
        if not request.form.get(field_name, "").strip():
            errors.append(message)
    if errors:
        for err in errors:
            flash(err)
        return None

    upload_filename = ficha["actividades_proceso_imagen"] if ficha else None
    uploaded_file = request.files.get("actividades_proceso_imagen")
    if uploaded_file and uploaded_file.filename:
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        _, ext = os.path.splitext(uploaded_file.filename.lower())
        if ext not in allowed_extensions:
            flash("Tipo de archivo no permitido. Solo se aceptan imágenes PNG, JPG, GIF o WEBP.")
            return None

        old_key = ficha.get("actividades_proceso_imagen") if ficha else None

        # 1. SUBIR archivo nuevo a S3 (fuera de transacción)
        new_key = storage.upload_file(uploaded_file, "fichas")
        if not new_key:
            flash("Error al subir la imagen al almacenamiento.")
            return None
        upload_filename = new_key

        # La BD se actualizará más abajo con el nuevo_key en data[actividades_proceso_imagen]
        # Si la BD falla, se limpia el archivo nuevo en el except del caller

    data = {
        "codigo_proceso": request.form.get("codigo_proceso", "").strip(),
        "nombre_proceso": request.form.get("nombre_proceso", "").strip(),
        "tipo_proceso": _optional_value("tipo_proceso"),
        "dueno_proceso": _optional_value("dueno_proceso"),
        "objetivo_proceso": request.form.get("objetivo_proceso", "").strip(),
        "objetivo_estrategico": _optional_value("objetivo_estrategico"),
        "proveedor_entrada": _optional_value("proveedor_entrada"),
        "elementos_entrada": _optional_value("elementos_entrada"),
        "producto": _optional_value("producto"),
        "receptor_producto": _optional_value("receptor_producto"),
        "actividades_proceso_imagen": upload_filename,
        "riesgos": _optional_value("riesgos"),
        "registros": _optional_value("registros"),
        "elaborado_por": request.form.get("elaborado_por", "").strip() or "GRUPO 8",
        "revisado_por": _optional_value("revisado_por"),
        "aprobado_por": _optional_value("aprobado_por"),
    }

    if ficha:
        old_key = ficha.get("actividades_proceso_imagen")
        repo.save_ficha_caracterizacion(data, ficha_id=ficha["id"])
    else:
        old_key = None
        repo.save_ficha_caracterizacion(data)

    # 3. ENCOLAR archivo anterior para borrado asíncrono (solo si se subió uno nuevo)
    if old_key and uploaded_file and uploaded_file.filename:
        repo.enqueue_pendiente(old_key)

    return data


@bp.route("/ficha-caracterizacion/nueva", methods=["GET", "POST"])
def ficha_caracterizacion_nueva():
    if request.method == "POST":
        if _save_ficha_form() is not None:
            flash("Ficha de caracterización registrada correctamente.")
            return redirect(url_for("main.fichas_caracterizacion"))
    return render_template(
        "ficha_caracterizacion_form.html",
        ficha=None,
        ficha_signed_url=None,
        form_title="Agregar ficha de caracterización",
        submit_label="Guardar ficha",
    )


@bp.route("/ficha-caracterizacion/<int:ficha_id>")
def ficha_caracterizacion_ver(ficha_id):
    ficha = repo.get_ficha_caracterizacion(ficha_id)
    if not ficha:
        abort(404)
    ficha_signed_url = (
        storage.get_signed_url(ficha["actividades_proceso_imagen"])
        if ficha.get("actividades_proceso_imagen")
        else None
    )
    return render_template("ficha_caracterizacion_view.html", ficha=ficha, ficha_signed_url=ficha_signed_url)


@bp.route("/ficha-caracterizacion/<int:ficha_id>/editar", methods=["GET", "POST"])
def ficha_caracterizacion_editar(ficha_id):
    ficha = repo.get_ficha_caracterizacion(ficha_id)
    if not ficha:
        abort(404)
    if request.method == "POST":
        if _save_ficha_form(ficha) is not None:
            flash("Ficha de caracterización actualizada correctamente.")
            return redirect(url_for("main.fichas_caracterizacion"))
    ficha_signed_url = (
        storage.get_signed_url(ficha["actividades_proceso_imagen"])
        if ficha.get("actividades_proceso_imagen")
        else None
    )
    return render_template(
        "ficha_caracterizacion_form.html",
        ficha=ficha,
        ficha_signed_url=ficha_signed_url,
        form_title="Editar ficha de caracterización",
        submit_label="Actualizar ficha",
    )


@bp.post("/api/limpiar-pendientes")
def limpiar_pendientes():
    """
    Procesador de cola de eliminación pendiente.
    Reclama trabajos, intenta borrar de S3, y reintenta con backoff si falla.
    """
    procesados = 0
    errores = 0

    pendientes = repo.claim_pendientes(limit=20)
    for p in pendientes:
        repo.mark_pendiente_procesando(p["id"])
        try:
            storage.delete_file(p["ruta_archivo"])
            repo.resolve_pendiente(p["id"])
            procesados += 1
        except Exception as e:
            repo.fail_pendiente(p["id"], str(e))
            errores += 1

    if procesados or errores:
        flash(f"Procesados: {procesados} eliminados, {errores} con error (reintentarán después).")
    else:
        flash("No hay archivos pendientes de eliminación.")

    return redirect(request.referrer or url_for("main.panel"))


@bp.post("/ficha-caracterizacion/<int:ficha_id>/eliminar")
def ficha_caracterizacion_eliminar(ficha_id):
    ficha = repo.get_ficha_caracterizacion(ficha_id)
    if not ficha:
        abort(404)
    old_key = ficha.get("actividades_proceso_imagen")
    # 1. ELIMINAR de BD primero
    repo.delete_ficha_caracterizacion(ficha_id)
    # 2. ENCOLAR archivo para borrado asíncrono
    if old_key:
        repo.enqueue_pendiente(old_key)
    flash("Ficha de caracterización eliminada.")
    return redirect(url_for("main.fichas_caracterizacion"))


@bp.route("/fichas-indicadores")
def fichas_indicadores():
    fichas = repo.get_fichas_indicadores()
    return render_template("ficha_indicadores_list.html", fichas=fichas)


@bp.route("/fichas-indicadores/nueva", methods=["GET", "POST"])
def ficha_indicadores_nueva():
    caracterizaciones = repo.get_fichas_caracterizacion()
    if request.method == "POST":
        errors = []
        if not request.form.get("ficha_caracterizacion_id"):
            errors.append("La ficha de caracterización es obligatoria.")
        if not request.form.get("producto", "").strip():
            errors.append("El producto es requerido.")
        if not request.form.get("nombre_indicador", "").strip():
            errors.append("El nombre del indicador es requerido.")
        if not request.form.get("tipo_indicador", "").strip():
            errors.append("El tipo de indicador es requerido.")
        if not request.form.get("responsable", "").strip():
            errors.append("El responsable es requerido.")
        if not request.form.get("sentido_esperado", "").strip():
            errors.append("El sentido esperado es requerido.")
        if not request.form.get("unidad_medida", "").strip():
            errors.append("La unidad de medida es requerida.")
        if not request.form.get("frecuencia", "").strip():
            errors.append("La frecuencia es requerida.")
        if not request.form.get("fuente_datos", "").strip():
            errors.append("La fuente de datos es requerida.")

        if errors:
            for err in errors:
                flash(err)
        else:
            ficha_caracterizacion = repo.get_ficha_caracterizacion(_safe_int(request.form.get("ficha_caracterizacion_id")))
            data = {
                "ficha_caracterizacion_id": _safe_int(request.form.get("ficha_caracterizacion_id")),
                "proceso": ficha_caracterizacion["nombre_proceso"] if ficha_caracterizacion else "",
                "producto": request.form.get("producto", "").strip(),
                "nombre_indicador": request.form.get("nombre_indicador", "").strip(),
                "tipo_indicador": request.form.get("tipo_indicador", "").strip(),
                "justificacion": request.form.get("justificacion", "").strip(),
                "responsable": request.form.get("responsable", "").strip(),
                "metodo_calculo": request.form.get("metodo_calculo", "").strip(),
                "sentido_esperado": request.form.get("sentido_esperado", "").strip(),
                "unidad_medida": request.form.get("unidad_medida", "").strip(),
                "frecuencia": request.form.get("frecuencia", "").strip(),
                "fuente_datos": request.form.get("fuente_datos", "").strip(),
                "valor_enero": request.form.get("valor_enero", "").strip() or None,
                "valor_febrero": request.form.get("valor_febrero", "").strip() or None,
                "valor_marzo": request.form.get("valor_marzo", "").strip() or None,
                "valor_abril": request.form.get("valor_abril", "").strip() or None,
                "valor_mayo": request.form.get("valor_mayo", "").strip() or None,
                "valor_junio": request.form.get("valor_junio", "").strip() or None,
                "elaborado_por": request.form.get("elaborado_por", "").strip() or "GRUPO 8",
                "revisado_por": request.form.get("revisado_por", "").strip() or None,
                "aprobado_por": request.form.get("aprobado_por", "").strip() or None,
            }
            repo.save_ficha_indicador(data)
            flash("Ficha de indicadores registrada correctamente.")
            return redirect(url_for("main.fichas_indicadores"))

    return render_template(
        "ficha_indicadores_form.html",
        ficha=None,
        caracterizaciones=caracterizaciones,
        form_title="Agregar ficha de indicadores",
        submit_label="Guardar ficha",
    )


@bp.route("/fichas-indicadores/<int:ficha_id>")
def ficha_indicadores_ver(ficha_id):
    ficha = repo.get_ficha_indicador(ficha_id)
    if not ficha:
        abort(404)
    return render_template("ficha_indicadores_view.html", ficha=ficha)


@bp.route("/fichas-indicadores/<int:ficha_id>/editar", methods=["GET", "POST"])
def ficha_indicadores_editar(ficha_id):
    ficha = repo.get_ficha_indicador(ficha_id)
    if not ficha:
        abort(404)
    caracterizaciones = repo.get_fichas_caracterizacion()
    if request.method == "POST":
        errors = []
        if not request.form.get("ficha_caracterizacion_id"):
            errors.append("La ficha de caracterización es obligatoria.")
        if not request.form.get("producto", "").strip():
            errors.append("El producto es requerido.")
        if not request.form.get("nombre_indicador", "").strip():
            errors.append("El nombre del indicador es requerido.")
        if not request.form.get("tipo_indicador", "").strip():
            errors.append("El tipo de indicador es requerido.")
        if not request.form.get("responsable", "").strip():
            errors.append("El responsable es requerido.")
        if not request.form.get("sentido_esperado", "").strip():
            errors.append("El sentido esperado es requerido.")
        if not request.form.get("unidad_medida", "").strip():
            errors.append("La unidad de medida es requerida.")
        if not request.form.get("frecuencia", "").strip():
            errors.append("La frecuencia es requerida.")
        if not request.form.get("fuente_datos", "").strip():
            errors.append("La fuente de datos es requerida.")

        if errors:
            for err in errors:
                flash(err)
        else:
            ficha_caracterizacion = repo.get_ficha_caracterizacion(_safe_int(request.form.get("ficha_caracterizacion_id")))
            data = {
                "ficha_caracterizacion_id": _safe_int(request.form.get("ficha_caracterizacion_id")),
                "proceso": ficha_caracterizacion["nombre_proceso"] if ficha_caracterizacion else "",
                "producto": request.form.get("producto", "").strip(),
                "nombre_indicador": request.form.get("nombre_indicador", "").strip(),
                "tipo_indicador": request.form.get("tipo_indicador", "").strip(),
                "justificacion": request.form.get("justificacion", "").strip(),
                "responsable": request.form.get("responsable", "").strip(),
                "metodo_calculo": request.form.get("metodo_calculo", "").strip(),
                "sentido_esperado": request.form.get("sentido_esperado", "").strip(),
                "unidad_medida": request.form.get("unidad_medida", "").strip(),
                "frecuencia": request.form.get("frecuencia", "").strip(),
                "fuente_datos": request.form.get("fuente_datos", "").strip(),
                "valor_enero": request.form.get("valor_enero", "").strip() or None,
                "valor_febrero": request.form.get("valor_febrero", "").strip() or None,
                "valor_marzo": request.form.get("valor_marzo", "").strip() or None,
                "valor_abril": request.form.get("valor_abril", "").strip() or None,
                "valor_mayo": request.form.get("valor_mayo", "").strip() or None,
                "valor_junio": request.form.get("valor_junio", "").strip() or None,
                "elaborado_por": request.form.get("elaborado_por", "").strip() or "GRUPO 8",
                "revisado_por": request.form.get("revisado_por", "").strip() or None,
                "aprobado_por": request.form.get("aprobado_por", "").strip() or None,
            }
            repo.save_ficha_indicador(data, ficha_id=ficha_id)
            flash("Ficha de indicadores actualizada correctamente.")
            return redirect(url_for("main.fichas_indicadores"))

    return render_template(
        "ficha_indicadores_form.html",
        ficha=ficha,
        caracterizaciones=caracterizaciones,
        form_title="Editar ficha de indicadores",
        submit_label="Actualizar ficha",
    )


@bp.post("/fichas-indicadores/<int:ficha_id>/eliminar")
def ficha_indicadores_eliminar(ficha_id):
    ficha = repo.get_ficha_indicador(ficha_id)
    if not ficha:
        abort(404)
    repo.delete_ficha_indicador(ficha_id)
    flash("Ficha de indicadores eliminada.")
    return redirect(url_for("main.fichas_indicadores"))


@bp.route("/mapa", methods=["GET", "POST"])
def mapa():
    mapa_registro = repo.get_mapa()
    if request.method == "POST":
        file = request.files.get("imagen")
        if not file or file.filename == "":
            flash("Por favor selecciona un archivo de imagen.")
            return redirect(url_for("main.mapa"))

        # Validar tipo de archivo
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in allowed_extensions:
            flash(f"Tipo de archivo no permitido. Tipos permitidos: {', '.join(allowed_extensions)}")
            return redirect(url_for("main.mapa"))

        # 1. SUBIR archivo nuevo a S3 (fuera de transacción)
        new_key = storage.upload_file(file, "mapas")
        if not new_key:
            flash("Error al subir la imagen al almacenamiento.")
            return redirect(url_for("main.mapa"))

        old_key = mapa_registro["imagen"] if mapa_registro else None

        # 2. GUARDAR en BD primero (la imagen nueva ya está en S3)
        try:
            repo.save_mapa(new_key)
        except Exception:
            # Si la BD falla, limpiar el archivo recién subido
            storage.delete_file(new_key)
            flash("Error al guardar en la base de datos.")
            return redirect(url_for("main.mapa"))

        # 3. ENCOLAR archivo anterior para borrado asíncrono (si existe)
        if old_key:
            repo.enqueue_pendiente(old_key)

        flash("Imagen del mapa actualizada correctamente.")
        return redirect(url_for("main.mapa"))

    mapa_signed_url = storage.get_signed_url(mapa_registro["imagen"]) if mapa_registro else None
    return render_template("mapa.html", mapa=mapa_registro, mapa_signed_url=mapa_signed_url)


@bp.route("/acciones", methods=["GET", "POST"])
def acciones():
    if request.method == "POST":
        objetivo_estrategico_id = _safe_int(request.form.get("objetivo_estrategico_id"))
        if not objetivo_estrategico_id:
            flash("Selecciona un objetivo estratégico válido.")
            return redirect(url_for("main.acciones"))
        repo.save_accion(
            {
                "objetivo_estrategico_id": objetivo_estrategico_id,
                "nombre": request.form["nombre"].strip(),
            },
            request.form.get("id") or None,
        )
        flash("Acción estratégica guardada.")
        return redirect(url_for("main.acciones"))

    return render_template(
        "acciones.html",
        objetivos=repo.get_objetivos(),
        acciones=repo.get_acciones(),
    )


@bp.post("/acciones/<int:accion_id>/eliminar")
def accion_eliminar(accion_id):
    repo.delete_accion(accion_id)
    flash("Acción estratégica eliminada.")
    return redirect(url_for("main.acciones"))


@bp.route("/metas-anuales", methods=["GET", "POST"])
def metas_anuales():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    if not _require_data(indicadores, gestiones):
        return _empty_state("Registra indicadores y gestiones antes de cargar metas anuales.")

    if request.method == "POST":
        meta_anual = _float_value("meta_anual")
        indicador_id = _safe_int(request.form.get("indicador_id"))
        gestion_id = _safe_int(request.form.get("gestion_id"))
        if meta_anual is not None:
            if indicador_id and gestion_id and 0 <= meta_anual <= 100:
                repo.save_meta_anual(
                    indicador_id,
                    gestion_id,
                    meta_anual,
                )
                flash("Meta anual guardada.")
            else:
                flash("La meta anual debe estar entre 0 y 100.")
        else:
            flash("Ingresa una meta anual válida.")
        return redirect(url_for("main.metas_anuales"))

    return render_template(
        "metas_anuales.html",
        indicadores=indicadores,
        gestiones=gestiones,
        gestion_id=repo.get_default_gestion_id(),
        metas_anuales=repo.get_metas_anuales(),
    )


@bp.post("/metas-anuales/<int:meta_anual_id>/eliminar")
def meta_anual_eliminar(meta_anual_id):
    repo.delete_meta_anual(meta_anual_id)
    flash("Meta anual eliminada.")
    return redirect(url_for("main.metas_anuales"))



@bp.route("/indicadores", methods=["GET", "POST"])
def indicadores():
    if request.method == "POST":
        prioridad = _safe_int(request.form.get("prioridad"))
        accion_estrategica_id = _safe_int(request.form.get("accion_estrategica_id"))
        if prioridad not in (1, 2, 3):
            flash("La prioridad debe estar entre 1 y 3.")
            return redirect(url_for("main.indicadores"))
        if not accion_estrategica_id:
            flash("Selecciona una acción estratégica válida.")
            return redirect(url_for("main.indicadores"))
        repo.save_indicador(
            {
                "accion_estrategica_id": accion_estrategica_id,
                "codigo": request.form["codigo"].strip(),
                "nombre_indicador": request.form["nombre_indicador"].strip(),
                "prioridad": prioridad,
                "sentido_esperado": request.form["sentido_esperado"],
                "formula": request.form["formula"].strip(),
                "tipo_agregacion": request.form["tipo_agregacion"],
            },
            request.form.get("id") or None,
        )
        flash("Indicador guardado.")
        return redirect(url_for("main.indicadores"))

    return render_template(
        "indicadores.html",
        indicadores=repo.get_indicadores(include_inactive=True),
        acciones=repo.get_acciones(),
    )


@bp.post("/indicadores/<int:indicador_id>/estado")
def indicador_estado(indicador_id):
    estado = _safe_int(request.form.get("estado"))
    if estado not in (0, 1):
        flash("Estado inválido.")
        return redirect(url_for("main.indicadores"))
    repo.toggle_indicador(indicador_id, estado)
    return redirect(url_for("main.indicadores"))


@bp.post("/indicadores/<int:indicador_id>/eliminar")
def indicador_eliminar(indicador_id):
    repo.delete_indicador(indicador_id)
    flash("Indicador eliminado.")
    return redirect(url_for("main.indicadores"))


@bp.route("/vinculacion", methods=["GET", "POST"])
def vinculacion():
    if request.method == "POST":
        indicador_id = _safe_int(request.form.get("indicador_id"))
        proceso_ids = request.form.getlist("proceso_ids")
        
        if not indicador_id:
            flash("Selecciona un indicador válido.")
            return redirect(url_for("main.vinculacion"))
        if not proceso_ids:
            flash("Selecciona al menos un proceso para vincular.")
            return redirect(url_for("main.vinculacion"))
            
        repo.save_indicador_procesos(indicador_id, proceso_ids)
        flash("Vinculación de procesos guardada correctamente.")
        return redirect(url_for("main.vinculacion"))

    # Indicadores que ya tienen procesos vinculados
    vinculaciones = repo.get_indicadores_con_procesos()
    for v in vinculaciones:
        linked = repo.get_procesos_by_indicador(v["id"])
        v["proceso_ids"] = [p["id"] for p in linked]
        v["procesos"] = linked

    # Indicadores libres (sin procesos)
    indicadores_libres = repo.get_indicadores_sin_procesos()
    procesos_list = repo.get_procesos()

    return render_template(
        "vinculacion.html",
        vinculaciones=vinculaciones,
        indicadores_libres=indicadores_libres,
        procesos=procesos_list
    )


@bp.post("/vinculacion/<int:indicador_id>/eliminar")
def vinculacion_eliminar(indicador_id):
    repo.save_indicador_procesos(indicador_id, [])
    flash("Vínculo de procesos eliminado.")
    return redirect(url_for("main.vinculacion"))


@bp.route("/lineas-base", methods=["GET", "POST"])
def lineas_base():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    if not _require_data(indicadores, gestiones):
        return _empty_state("Registra indicadores y gestiones antes de cargar líneas base.")

    if request.method == "POST":
        linea_base = _float_value("linea_base")
        indicador_id = _safe_int(request.form.get("indicador_id"))
        gestion_id = _safe_int(request.form.get("gestion_id"))
        if linea_base is not None:
            if indicador_id and gestion_id and 0 <= linea_base <= 100:
                repo.save_linea_base(
                    indicador_id,
                    gestion_id,
                    linea_base,
                )
                flash("Línea base guardada.")
            else:
                flash("La línea base debe estar entre 0 y 100.")
        else:
            flash("Ingresa una línea base válida.")
        return redirect(url_for("main.lineas_base"))

    return render_template(
        "lineas_base.html",
        indicadores=indicadores,
        gestiones=gestiones,
        gestion_id=repo.get_default_gestion_id(),
        lineas=repo.get_lineas_base(),
    )


@bp.post("/lineas-base/<int:linea_base_id>/eliminar")
def linea_base_eliminar(linea_base_id):
    repo.delete_linea_base(linea_base_id)
    flash("Línea base eliminada.")
    return redirect(url_for("main.lineas_base"))



@bp.route("/metas-valores", methods=["GET", "POST"])
def metas_valores():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    if not _require_data(indicadores, gestiones):
        return _empty_state("Registra indicadores y gestiones antes de cargar metas y valores.")

    gestion_id = _safe_int(
        request.form.get("gestion_id")
        or request.args.get("gestion_id")
        or repo.get_default_gestion_id(),
        repo.get_default_gestion_id(),
    )
    indicador_id = _safe_int(
        request.form.get("indicador_id")
        or request.args.get("indicador_id")
        or indicadores[0]["id"],
        indicadores[0]["id"],
    )

    from datetime import datetime
    now = datetime.now()
    selected_gestion = next((g for g in gestiones if g["id"] == gestion_id), None)
    gestion_year = int(selected_gestion["nombre"]) if selected_gestion else now.year

    if request.method == "POST":
        mes_id = _safe_int(request.form.get("mes_id"))
        meta = _float_value("meta_mensual")
        valor = _float_value("valor_obtenido")
        errors = []
        if not mes_id:
            errors.append("Selecciona un mes válido.")
        
        # Validar si el mes ya ha transcurrido
        if mes_id:
            mes = next((m for m in repo.get_meses() if m["id"] == mes_id), None)
            if mes:
                numero_mes = mes["numero_mes"]
                ha_pasado = (gestion_year < now.year) or (gestion_year == now.year and numero_mes < now.month)
                if ha_pasado:
                    errors.append("No se pueden modificar metas o valores de meses ya transcurridos.")

        if not errors:
            if meta is not None:
                if 0 <= meta <= 100:
                    repo.save_meta(indicador_id, gestion_id, mes_id, meta)
                else:
                    errors.append("La meta mensual debe estar entre 0 y 100.")
            if valor is not None:
                if 0 <= valor <= 100:
                    repo.save_valor(indicador_id, gestion_id, mes_id, valor)
                else:
                    errors.append("El valor obtenido debe estar entre 0 y 100.")

        if errors:
            for err in errors:
                flash(err)
        else:
            flash("Meta / valor guardado.")
        return redirect(url_for("main.metas_valores", indicador_id=indicador_id, gestion_id=gestion_id))

    registros = repo.get_metas_valores(indicador_id, gestion_id)
    for r in registros:
        r["ha_pasado"] = (gestion_year < now.year) or (gestion_year == now.year and r["numero_mes"] < now.month)

    meses = repo.get_meses()
    for m in meses:
        m["ha_pasado"] = (gestion_year < now.year) or (gestion_year == now.year and m["numero_mes"] < now.month)

    meta_anual = repo.get_meta_anual(indicador_id, gestion_id)
    chart_data = services.build_metas_chart(registros, meta_anual)

    return render_template(
        "metas_valores.html",
        indicadores=indicadores,
        gestiones=gestiones,
        meses=meses,
        registros=registros,
        meta_anual=meta_anual,
        indicador_id=indicador_id,
        gestion_id=gestion_id,
        **chart_data,
    )


@bp.route("/resumen")
def resumen():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    if not _require_data(indicadores, gestiones):
        return _empty_state("Registra indicadores y gestiones antes de ver el resumen.")

    gestion_id = _safe_int(request.args.get("gestion_id"), repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    if not _require_data(periodos):
        return _empty_state("No hay periodos registrados para la gestión seleccionada.")
    indicador_id = _safe_int(request.args.get("indicador_id"), indicadores[0]["id"])
    periodo_id = _safe_int(request.args.get("periodo_id"), periodos[0]["id"])
    periodo = next((p for p in periodos if p["id"] == periodo_id), periodos[0])
    gestion = next((g for g in gestiones if g["id"] == gestion_id), gestiones[0])
    indicador = repo.get_indicador(indicador_id)
    registros = repo.get_metas_valores(indicador_id, gestion_id, periodo_id)
    resumen_periodo = services.summarize_period(indicador, registros)
    cumplimiento = resumen_periodo["cumplimiento"]

    estado_avance = _estado_avance(cumplimiento)
    alerta_cierre = _alerta_por_estado(estado_avance, gestion["nombre"], periodo["mes_fin"])
    meta_anual = repo.get_meta_anual(indicador_id, gestion_id)
    chart_data = services.build_metas_chart(registros, meta_anual)

    return render_template(
        "resumen.html",
        indicadores=indicadores,
        gestiones=gestiones,
        periodos=periodos,
        indicador_id=indicador_id,
        gestion_id=gestion_id,
        periodo_id=periodo_id,
        indicador=indicador,
        registros=registros,
        meta_periodo=resumen_periodo["meta_periodo"],
        valor_periodo=resumen_periodo["valor_periodo"],
        cumplimiento=cumplimiento,
        estado_avance=estado_avance,
        alerta_cierre=alerta_cierre,
        periodo=periodo,
        **chart_data,
    )


@bp.route("/avances", methods=["GET", "POST"])
def avances():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    if not _require_data(indicadores, gestiones):
        return _empty_state("Registra indicadores y gestiones antes de calcular avances.")

    gestion_id = _safe_int(request.values.get("gestion_id"), repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    if not _require_data(periodos):
        return _empty_state("No hay periodos registrados para la gestión seleccionada.")
    indicador_value = request.values.get("indicador_id") or ""
    indicador_id = _safe_int(indicador_value) if indicador_value else None

    if request.method == "POST":
        periodo_id = _safe_int(request.form.get("periodo_id"))
        if not periodo_id:
            flash("Selecciona un periodo válido.")
            return redirect(url_for("main.avances", indicador_id=indicador_value, gestion_id=gestion_id))
        resultado = repo.calcular_avance_tipo_1(
            gestion_id,
            periodo_id,
        )
        if resultado["periodo"]:
            flash(
                "Avance Tipo 1 calculado para "
                f"{resultado['periodo']} usando {resultado['mes']}. "
                f"Calculados: {resultado['calculados']}. "
                f"Omitidos: {resultado['omitidos']}."
            )
        else:
            flash("No se pudo calcular: el periodo no pertenece a la gestión seleccionada.")
        return redirect(url_for("main.avances", indicador_id=indicador_value, gestion_id=gestion_id))

    avances = repo.get_avances(gestion_id, indicador_id)
    for avance in avances:
        resultado = float(avance["resultado"])
        avance["resultado_vista"] = services.limitar_porcentaje(resultado)
        avance["estado"] = _estado_avance(resultado)
        avance["alerta"] = _alerta_por_estado(avance["estado"], avance["gestion"], avance["mes_fin"])

    avances_acciones = repo.get_avances_acciones(gestion_id)
    for aa in avances_acciones:
        res = float(aa["resultado"])
        aa["resultado_vista"] = services.limitar_porcentaje(res)
        aa["estado"] = _estado_avance(res)
        aa["alerta"] = _alerta_por_estado(aa["estado"], aa["gestion"], aa["mes_fin"])

    avances_objetivos = repo.get_avances_objetivos(gestion_id)
    for ao in avances_objetivos:
        res = float(ao["resultado"])
        ao["resultado_vista"] = services.limitar_porcentaje(res)
        ao["estado"] = _estado_avance(res)
        ao["alerta"] = _alerta_por_estado(ao["estado"], ao["gestion"], ao["mes_fin"])

    return render_template(
        "avances.html",
        indicadores=indicadores,
        gestiones=gestiones,
        periodos=periodos,
        indicador_id=indicador_id,
        gestion_id=gestion_id,
        avances=avances,
        avances_acciones=avances_acciones,
        avances_objetivos=avances_objetivos,
    )


@bp.route("/avance-tipo1", methods=["GET"])
def avance_tipo1():
    """
    Ruta para visualizar el reporte de Avance Tipo 1 basado en formato CEPLAN A11.
    Muestra seguimiento mensual de indicadores agrupados por objetivo y acción estratégica.
    """
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    
    if not _require_data(indicadores, gestiones):
        return _empty_state("Registra indicadores y gestiones antes de visualizar avances.")
    
    # Obtener valores por defecto
    gestion_id = _safe_int(request.values.get("gestion_id"), repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    
    if not _require_data(periodos):
        return _empty_state("No hay periodos registrados para la gestión seleccionada.")
    
    # Usar el primer período por defecto
    periodo_id = _safe_int(request.values.get("periodo_id")) or (periodos[0]["id"] if periodos else None)
    
    # Obtener datos del reporte
    data = None
    if periodo_id:
        data = reporte_ceplan_service.get_avance_tipo1_data(gestion_id, periodo_id)
    
    return render_template(
        "avance_tipo1.html",
        gestiones=gestiones,
        periodos=periodos,
        gestion_id=gestion_id,
        periodo_id=periodo_id,
        data=data,
    )


@bp.post("/api/ai/chat")
def api_ai_chat():
    data = request.json or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    # Obtener gestión activa
    gestion_id = repo.get_default_gestion_id()
    gestiones = repo.get_gestiones()
    gestion = next((g for g in gestiones if g["id"] == gestion_id), None)
    
    # Obtener periodos de esta gestion
    periodos = repo.get_periodos(gestion_id)
    periodo_id = periodos[0]["id"] if periodos else 3
    
    # Consultar datos de contexto de la base de datos (SOLO lectura)
    indicadores = repo.get_panel_seguimiento(gestion_id, periodo_id)
    procesos = repo.get_procesos()
    objetivos = repo.get_objetivos()

    system_instruction_add = (
        "\nEl chat es solo consultivo. Si el usuario pide vincular indicadores con procesos, "
        "indícale que debe hacerlo desde la pantalla tradicional de Vinculación. "
        "No generes enlaces select:, no pidas confirmación para guardar y no afirmes que se guardaron cambios desde el chat."
    )
    
    # Obtener todas las metas mensuales y valores obtenidos de la gestión activa
    valores_mensuales = repo.fetch_all(
        """
        SELECT i.codigo, m.nombre AS mes, mm.meta_mensual, vo.valor_obtenido
        FROM indicadores i
        JOIN meses m
        LEFT JOIN metas_mensuales mm ON mm.indicador_id = i.id AND mm.mes_id = m.id AND mm.gestion_id = %s
        LEFT JOIN valores_obtenidos vo ON vo.indicador_id = i.id AND vo.mes_id = m.id AND vo.gestion_id = %s
        WHERE i.estado = 1 AND (mm.meta_mensual IS NOT NULL OR vo.valor_obtenido IS NOT NULL)
        ORDER BY i.codigo, m.numero_mes
        """,
        (gestion_id, gestion_id)
    )

    # Obtener líneas base de esta gestión
    lineas_base = repo.fetch_all(
        """
        SELECT i.codigo, lb.linea_base
        FROM lineas_base lb
        JOIN indicadores i ON lb.indicador_id = i.id
        WHERE lb.gestion_id = %s
        """,
        (gestion_id,)
    )

    vinculaciones = repo.get_vinculaciones_completas()
    
    context_data = {
        "gestion": gestion["nombre"] if gestion else "N/A",
        "objetivos": [{"id": o["id"], "nombre": o["nombre"]} for o in objetivos],
        "procesos": [
            {
                "codigo": p["codigo_proceso"],
                "nombre": p["nombre_proceso"],
                "tipo": p["tipo_proceso"],
                "producto": p["producto_proceso"]
            } for p in procesos
        ],
        "indicadores": [
            {
                "codigo": i["codigo"],
                "nombre": i["nombre_indicador"],
                "meta_anual": f"{i['meta_anual']:.2f}" if i["meta_anual"] is not None else "Sin dato",
                "avance_tipo_1": f"{i['avance_tipo_1']:.2f}%" if i["avance_tipo_1"] is not None else "Sin dato"
            } for i in indicadores
        ],
        "lineas_base": [
            {
                "codigo_indicador": lb["codigo"],
                "linea_base": f"{lb['linea_base']:.2f}" if lb["linea_base"] is not None else "N/A"
            } for lb in lineas_base
        ],
        "valores_mensuales": [
            {
                "codigo_indicador": vm["codigo"],
                "mes": vm["mes"],
                "meta_mensual": f"{vm['meta_mensual']:.2f}" if vm["meta_mensual"] is not None else "N/A",
                "valor_obtenido": f"{vm['valor_obtenido']:.2f}" if vm["valor_obtenido"] is not None else "N/A"
            } for vm in valores_mensuales
        ],
        "vinculaciones_actuales": [
            {
                "indicador": vc["codigo_indicador"],
                "nombre_indicador": vc["nombre_indicador"],
                "proceso": vc["codigo_proceso"],
                "nombre_proceso": vc["nombre_proceso"]
            } for vc in vinculaciones
        ]
    }

    # Llamar a Gemini
    response_text = ai_service.consultar_asistente_wizard(message, history, context_data, system_instruction_add)
    
    return {"response": response_text}
