def limitar_porcentaje(valor):
    if valor is None:
        return None
    return min(float(valor), 100)


def build_metas_chart(registros, meta_anual):
    return {
        "chart_labels": [row["mes"] for row in registros],
        "chart_metas": [
            float(row["meta_mensual"]) if row["meta_mensual"] is not None else None
            for row in registros
        ],
        "chart_valores": [
            float(row["valor_obtenido"]) if row["valor_obtenido"] is not None else None
            for row in registros
        ],
        "chart_meta_anual": [
            float(meta_anual["meta_anual"]) if meta_anual else None
            for _ in registros
        ],
        "chart_cumplimiento": [
            round(limitar_porcentaje(float(row["valor_obtenido"]) / float(row["meta_mensual"]) * 100), 2)
            if row["meta_mensual"] not in (None, 0) and row["valor_obtenido"] is not None
            else None
            for row in registros
        ],
    }


def summarize_period(indicador, registros):
    metas = [float(r["meta_mensual"]) for r in registros if r["meta_mensual"] is not None]
    valores = [float(r["valor_obtenido"]) for r in registros if r["valor_obtenido"] is not None]
    if indicador["tipo_agregacion"] == "NO_AGREGABLE":
        meta_periodo = (
            float(registros[-1]["meta_mensual"])
            if registros and registros[-1]["meta_mensual"] is not None
            else None
        )
        valor_periodo = (
            float(registros[-1]["valor_obtenido"])
            if registros and registros[-1]["valor_obtenido"] is not None
            else None
        )
    else:
        meta_periodo = sum(metas) if metas else None
        valor_periodo = sum(valores) if valores else None

    cumplimiento = None
    if meta_periodo and valor_periodo is not None:
        cumplimiento = limitar_porcentaje(valor_periodo / meta_periodo * 100)

    return {
        "meta_periodo": meta_periodo,
        "valor_periodo": valor_periodo,
        "cumplimiento": cumplimiento,
    }
