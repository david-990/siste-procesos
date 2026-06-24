from calendar import monthrange
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import repositories as repo


bp = Blueprint("main", __name__)


def _float_value(name):
    value = request.form.get(name, "").strip().replace(",", ".")
    return float(value) if value else None


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
        texto = f"Faltan {dias} dias para el cierre"
        clase = "bg-blue-50 text-blue-700 border-blue-200"
    elif dias == 0:
        texto = "El periodo cierra hoy"
        clase = "bg-amber-50 text-amber-700 border-amber-200"
    else:
        texto = f"Cerrado hace {abs(dias)} dias"
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


def _limitar_porcentaje(valor):
    if valor is None:
        return None
    return min(float(valor), 100)


@bp.route("/")
def index():
    return redirect(url_for("main.panel"))


@bp.route("/panel")
def panel():
    gestiones = repo.get_gestiones()
    gestion_id = int(request.args.get("gestion_id") or repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    periodo_id = int(request.args.get("periodo_id") or periodos[0]["id"])
    periodo = next((p for p in periodos if p["id"] == periodo_id), periodos[0])
    gestion = next((g for g in gestiones if g["id"] == gestion_id), gestiones[0])
    seguimiento = repo.get_panel_seguimiento(gestion_id, periodo_id)
    evolucion = repo.get_panel_evolucion(gestion_id, periodo_id)
    alerta_cierre = _alerta_cierre(gestion["nombre"], periodo["mes_fin"])

    for fila in seguimiento:
        avance = float(fila["avance_tipo_1"]) if fila["avance_tipo_1"] is not None else None
        fila["estado"] = _estado_avance(avance)
        fila["alerta"] = _alerta_por_estado(fila["estado"], gestion["nombre"], periodo["mes_fin"])
        fila["avance_tipo_1_vista"] = _limitar_porcentaje(avance)

    total_indicadores = len(seguimiento)
    resultados = [float(f["avance_tipo_1"]) for f in seguimiento if f["avance_tipo_1"] is not None]
    resultados_vista = [_limitar_porcentaje(valor) for valor in resultados]
    avance_promedio = sum(resultados_vista) / len(resultados_vista) if resultados_vista else None

    conteo_estados = {"Critico": 0, "En seguimiento": 0, "Concluido": 0, "Sin dato": 0}
    for fila in seguimiento:
        conteo_estados[fila["estado"]["nombre"]] += 1

    alertas_activas = conteo_estados["Critico"] + conteo_estados["En seguimiento"]
    pendientes = [
        fila
        for fila in seguimiento
        if fila["estado"]["nombre"] != "Concluido"
    ]
    total_meta_cierre = sum(float(f["meta_cierre"]) for f in seguimiento if f["meta_cierre"] is not None)
    total_meta_anual = sum(float(f["meta_anual"]) for f in seguimiento if f["meta_anual"] is not None)
    total_valor_cierre = sum(float(f["valor_cierre"]) for f in seguimiento if f["valor_cierre"] is not None)

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
        sin_dato=conteo_estados["Sin dato"],
        avance_promedio=avance_promedio,
        alertas_activas=alertas_activas,
        concluidos=conteo_estados["Concluido"],
        pendientes=pendientes,
        seguimiento=seguimiento,
        bar_labels=[f["codigo"] for f in seguimiento if f["avance_tipo_1"] is not None],
        bar_values=[round(_limitar_porcentaje(f["avance_tipo_1"]), 2) for f in seguimiento if f["avance_tipo_1"] is not None],
        comparison_labels=["Logro esperado", "Meta anual", "Valor obtenido"],
        comparison_values=[
            round(total_meta_cierre, 2),
            round(total_meta_anual, 2),
            round(total_valor_cierre, 2),
        ],
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
    )


@bp.route("/acciones", methods=["GET", "POST"])
def acciones():
    if request.method == "POST":
        repo.save_accion(
            {
                "indicador_id": int(request.form["indicador_id"]),
                "codigo": request.form["codigo"].strip(),
                "nombre_accion": request.form["nombre_accion"].strip(),
                "descripcion": _optional_value("descripcion"),
                "fecha_inicio": _optional_value("fecha_inicio"),
                "fecha_fin": _optional_value("fecha_fin"),
            },
            request.form.get("id") or None,
        )
        flash("Accion guardada.")
        return redirect(url_for("main.acciones"))

    return render_template(
        "acciones.html",
        indicadores=repo.get_indicadores(),
        acciones=repo.get_acciones(),
    )


@bp.post("/acciones/<int:accion_id>/eliminar")
def accion_eliminar(accion_id):
    repo.delete_accion(accion_id)
    flash("Accion eliminada.")
    return redirect(url_for("main.acciones"))


@bp.route("/metas-anuales", methods=["GET", "POST"])
def metas_anuales():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()

    if request.method == "POST":
        meta_anual = _float_value("meta_anual")
        if meta_anual is not None:
            repo.save_meta_anual(
                int(request.form["indicador_id"]),
                int(request.form["gestion_id"]),
                meta_anual,
            )
            flash("Meta anual guardada.")
        else:
            flash("Ingresa una meta anual valida.")
        return redirect(url_for("main.metas_anuales"))

    return render_template(
        "metas_anuales.html",
        indicadores=indicadores,
        gestiones=gestiones,
        gestion_id=repo.get_default_gestion_id(),
        metas_anuales=repo.get_metas_anuales(),
    )



@bp.route("/indicadores", methods=["GET", "POST"])
def indicadores():
    if request.method == "POST":
        repo.save_indicador(
            {
                "codigo": request.form["codigo"].strip(),
                "nombre_indicador": request.form["nombre_indicador"].strip(),
                "prioridad": int(request.form["prioridad"]),
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
    )


@bp.post("/indicadores/<int:indicador_id>/estado")
def indicador_estado(indicador_id):
    repo.toggle_indicador(indicador_id, int(request.form["estado"]))
    return redirect(url_for("main.indicadores"))


@bp.post("/indicadores/<int:indicador_id>/eliminar")
def indicador_eliminar(indicador_id):
    repo.delete_indicador(indicador_id)
    flash("Indicador eliminado.")
    return redirect(url_for("main.indicadores"))


@bp.route("/lineas-base", methods=["GET", "POST"])
def lineas_base():
    if request.method == "POST":
        repo.save_linea_base(
            int(request.form["indicador_id"]),
            int(request.form["gestion_id"]),
            _float_value("linea_base"),
        )
        flash("Linea base guardada.")
        return redirect(url_for("main.lineas_base"))

    return render_template(
        "lineas_base.html",
        indicadores=repo.get_indicadores(),
        gestiones=repo.get_gestiones(),
        gestion_id=repo.get_default_gestion_id(),
        lineas=repo.get_lineas_base(),
    )



@bp.route("/metas-valores", methods=["GET", "POST"])
def metas_valores():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    gestion_id = int(
        request.form.get("gestion_id")
        or request.args.get("gestion_id")
        or repo.get_default_gestion_id()
    )
    indicador_id = int(
        request.form.get("indicador_id")
        or request.args.get("indicador_id")
        or indicadores[0]["id"]
    )

    if request.method == "POST":
        mes_id = int(request.form["mes_id"])
        meta = _float_value("meta_mensual")
        valor = _float_value("valor_obtenido")
        if meta is not None:
            repo.save_meta(indicador_id, gestion_id, mes_id, meta)
        if valor is not None:
            repo.save_valor(indicador_id, gestion_id, mes_id, valor)
        flash("Meta / valor guardado.")
        return redirect(url_for("main.metas_valores", indicador_id=indicador_id, gestion_id=gestion_id))

    registros = repo.get_metas_valores(indicador_id, gestion_id)
    meta_anual = repo.get_meta_anual(indicador_id, gestion_id)
    chart_labels = [row["mes"] for row in registros]
    chart_metas = [float(row["meta_mensual"]) if row["meta_mensual"] is not None else None for row in registros]
    chart_valores = [float(row["valor_obtenido"]) if row["valor_obtenido"] is not None else None for row in registros]
    chart_meta_anual = [
        float(meta_anual["meta_anual"]) if meta_anual else None
        for _ in registros
    ]
    chart_cumplimiento = [
        round(_limitar_porcentaje(float(row["valor_obtenido"]) / float(row["meta_mensual"]) * 100), 2)
        if row["meta_mensual"] not in (None, 0) and row["valor_obtenido"] is not None
        else None
        for row in registros
    ]

    return render_template(
        "metas_valores.html",
        indicadores=indicadores,
        gestiones=gestiones,
        meses=repo.get_meses(),
        registros=registros,
        meta_anual=meta_anual,
        indicador_id=indicador_id,
        gestion_id=gestion_id,
        chart_labels=chart_labels,
        chart_metas=chart_metas,
        chart_valores=chart_valores,
        chart_meta_anual=chart_meta_anual,
        chart_cumplimiento=chart_cumplimiento,
    )


@bp.route("/resumen")
def resumen():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    gestion_id = int(request.args.get("gestion_id") or repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    indicador_id = int(request.args.get("indicador_id") or indicadores[0]["id"])
    periodo_id = int(request.args.get("periodo_id") or periodos[0]["id"])
    periodo = next((p for p in periodos if p["id"] == periodo_id), periodos[0])
    gestion = next((g for g in gestiones if g["id"] == gestion_id), gestiones[0])
    indicador = repo.get_indicador(indicador_id)
    registros = repo.get_metas_valores(indicador_id, gestion_id, periodo_id)

    metas = [float(r["meta_mensual"]) for r in registros if r["meta_mensual"] is not None]
    valores = [float(r["valor_obtenido"]) for r in registros if r["valor_obtenido"] is not None]
    if indicador["tipo_agregacion"] == "NO_AGREGABLE":
        meta_periodo = sum(metas) / len(metas) if metas else None
        valor_periodo = sum(valores) / len(valores) if valores else None
    else:
        meta_periodo = sum(metas) if metas else None
        valor_periodo = sum(valores) if valores else None

    cumplimiento = None
    if meta_periodo and valor_periodo is not None:
        cumplimiento = _limitar_porcentaje(valor_periodo / meta_periodo * 100)

    estado_avance = _estado_avance(cumplimiento)
    alerta_cierre = _alerta_por_estado(estado_avance, gestion["nombre"], periodo["mes_fin"])

    chart_labels = [row["mes"] for row in registros]
    chart_metas = [float(row["meta_mensual"]) if row["meta_mensual"] is not None else None for row in registros]
    chart_valores = [float(row["valor_obtenido"]) if row["valor_obtenido"] is not None else None for row in registros]
    meta_anual = repo.get_meta_anual(indicador_id, gestion_id)
    chart_meta_anual = [
        float(meta_anual["meta_anual"]) if meta_anual else None
        for _ in registros
    ]
    chart_cumplimiento = [
        round(_limitar_porcentaje(float(row["valor_obtenido"]) / float(row["meta_mensual"]) * 100), 2)
        if row["meta_mensual"] not in (None, 0) and row["valor_obtenido"] is not None
        else None
        for row in registros
    ]

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
        meta_periodo=meta_periodo,
        valor_periodo=valor_periodo,
        cumplimiento=cumplimiento,
        estado_avance=estado_avance,
        alerta_cierre=alerta_cierre,
        periodo=periodo,
        chart_labels=chart_labels,
        chart_metas=chart_metas,
        chart_valores=chart_valores,
        chart_meta_anual=chart_meta_anual,
        chart_cumplimiento=chart_cumplimiento,
    )


@bp.route("/avances", methods=["GET", "POST"])
def avances():
    indicadores = repo.get_indicadores()
    gestiones = repo.get_gestiones()
    gestion_id = int(request.values.get("gestion_id") or repo.get_default_gestion_id())
    periodos = repo.get_periodos(gestion_id)
    indicador_value = request.values.get("indicador_id") or ""
    indicador_id = int(indicador_value) if indicador_value else None

    if request.method == "POST":
        resultado = repo.calcular_avance_tipo_1(
            gestion_id,
            int(request.form["periodo_id"]),
        )
        if resultado["periodo"]:
            flash(
                "Avance Tipo 1 calculado para "
                f"{resultado['periodo']} usando {resultado['mes']}. "
                f"Calculados: {resultado['calculados']}. "
                f"Omitidos: {resultado['omitidos']}."
            )
        else:
            flash("No se pudo calcular: el periodo no pertenece a la gestion seleccionada.")
        return redirect(url_for("main.avances", indicador_id=indicador_value, gestion_id=gestion_id))

    avances = repo.get_avances(gestion_id, indicador_id)
    for avance in avances:
        resultado = float(avance["resultado"])
        avance["resultado_vista"] = _limitar_porcentaje(resultado)
        avance["estado"] = _estado_avance(resultado)
        avance["alerta"] = _alerta_por_estado(avance["estado"], avance["gestion"], avance["mes_fin"])

    return render_template(
        "avances.html",
        indicadores=indicadores,
        gestiones=gestiones,
        periodos=periodos,
        indicador_id=indicador_id,
        gestion_id=gestion_id,
        avances=avances,
    )
