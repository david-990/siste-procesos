from datetime import datetime

from app.db import execute, fetch_all, fetch_one


def get_gestiones():
    return fetch_all(
        "SELECT id, nombre, CAST(nombre AS UNSIGNED) AS anio FROM gestiones ORDER BY nombre"
    )


def get_default_gestion_id():
    gestiones = get_gestiones()
    current_year = datetime.now().year
    for gestion in gestiones:
        if gestion["anio"] == current_year:
            return gestion["id"]
    return gestiones[0]["id"] if gestiones else None


def get_meses():
    return fetch_all("SELECT id, nombre, numero_mes FROM meses ORDER BY numero_mes")


def get_periodos(gestion_id):
    return fetch_all(
        """
        SELECT p.id, p.gestion_id, p.nombre,
               p.mes_inicio_id, p.mes_fin_id,
               mi.numero_mes AS mes_inicio,
               mf.numero_mes AS mes_fin,
               mi.nombre AS mes_inicio_nombre,
               mf.nombre AS mes_fin_nombre
        FROM periodos p
        JOIN meses mi ON p.mes_inicio_id = mi.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        WHERE p.gestion_id = %s
        ORDER BY mi.numero_mes
        """,
        (gestion_id,),
    )


def get_indicadores(include_inactive=False):
    where = "" if include_inactive else "WHERE estado = 1"
    return fetch_all(
        f"""
        SELECT id, codigo, nombre_indicador, prioridad, sentido_esperado,
               formula, tipo_agregacion, estado
        FROM indicadores
        {where}
        ORDER BY codigo
        """
    )


def get_indicador(indicador_id):
    return fetch_one("SELECT * FROM indicadores WHERE id = %s", (indicador_id,))


def save_indicador(data, indicador_id=None):
    params = (
        data["codigo"],
        data["nombre_indicador"],
        data["prioridad"],
        data["sentido_esperado"],
        data["formula"],
        data["tipo_agregacion"],
    )
    if indicador_id:
        execute(
            """
            UPDATE indicadores
            SET codigo=%s, nombre_indicador=%s, prioridad=%s,
                sentido_esperado=%s, formula=%s, tipo_agregacion=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (*params, indicador_id),
        )
        return indicador_id
    return execute(
        """
        INSERT INTO indicadores
            (codigo, nombre_indicador, prioridad, sentido_esperado, formula, tipo_agregacion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        params,
    )


def toggle_indicador(indicador_id, estado):
    execute(
        "UPDATE indicadores SET estado=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
        (estado, indicador_id),
    )


def delete_indicador(indicador_id):
    execute("DELETE FROM indicadores WHERE id = %s", (indicador_id,))


def get_acciones():
    return fetch_all(
        """
        SELECT a.id, a.indicador_id, a.codigo, a.nombre_accion,
               a.descripcion, a.fecha_inicio, a.fecha_fin,
               i.codigo AS indicador_codigo,
               i.nombre_indicador
        FROM acciones a
        JOIN indicadores i ON a.indicador_id = i.id
        ORDER BY i.codigo, a.codigo
        """
    )


def save_accion(data, accion_id=None):
    params = (
        data["indicador_id"],
        data["codigo"],
        data["nombre_accion"],
        data["descripcion"],
        data["fecha_inicio"],
        data["fecha_fin"],
    )
    if accion_id:
        execute(
            """
            UPDATE acciones
            SET indicador_id=%s, codigo=%s, nombre_accion=%s,
                descripcion=%s, fecha_inicio=%s, fecha_fin=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (*params, accion_id),
        )
        return accion_id
    return execute(
        """
        INSERT INTO acciones
            (indicador_id, codigo, nombre_accion, descripcion, fecha_inicio, fecha_fin)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        params,
    )


def delete_accion(accion_id):
    execute("DELETE FROM acciones WHERE id = %s", (accion_id,))


def get_lineas_base(indicador_id=None):
    params = ()
    where = ""
    if indicador_id:
        where = "WHERE lb.indicador_id = %s"
        params = (indicador_id,)
    return fetch_all(
        f"""
        SELECT lb.id, lb.indicador_id, lb.gestion_id, lb.linea_base,
               i.codigo, i.nombre_indicador, g.nombre AS gestion
        FROM lineas_base lb
        JOIN indicadores i ON lb.indicador_id = i.id
        JOIN gestiones g ON lb.gestion_id = g.id
        {where}
        ORDER BY i.codigo, g.nombre
        """,
        params,
    )


def save_linea_base(indicador_id, gestion_id, linea_base):
    execute(
        """
        INSERT INTO lineas_base (indicador_id, gestion_id, linea_base)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE linea_base = VALUES(linea_base)
        """,
        (indicador_id, gestion_id, linea_base),
    )


def save_meta(indicador_id, gestion_id, mes_id, meta):
    execute(
        """
        INSERT INTO metas_mensuales (indicador_id, gestion_id, mes_id, meta_mensual)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE meta_mensual = VALUES(meta_mensual)
        """,
        (indicador_id, gestion_id, mes_id, meta),
    )


def get_meta_anual(indicador_id, gestion_id):
    return fetch_one(
        """
        SELECT id, indicador_id, gestion_id, meta_anual
        FROM metas_anuales
        WHERE indicador_id = %s AND gestion_id = %s
        """,
        (indicador_id, gestion_id),
    )


def get_metas_anuales(indicador_id=None):
    params = ()
    where = ""
    if indicador_id:
        where = "WHERE ma.indicador_id = %s"
        params = (indicador_id,)
    return fetch_all(
        f"""
        SELECT ma.id, ma.indicador_id, ma.gestion_id, ma.meta_anual,
               i.codigo, i.nombre_indicador, g.nombre AS gestion
        FROM metas_anuales ma
        JOIN indicadores i ON ma.indicador_id = i.id
        JOIN gestiones g ON ma.gestion_id = g.id
        {where}
        ORDER BY i.codigo, g.nombre
        """,
        params,
    )


def save_meta_anual(indicador_id, gestion_id, meta_anual):
    execute(
        """
        INSERT INTO metas_anuales (indicador_id, gestion_id, meta_anual)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE meta_anual = VALUES(meta_anual)
        """,
        (indicador_id, gestion_id, meta_anual),
    )


def save_valor(indicador_id, gestion_id, mes_id, valor):
    execute(
        """
        INSERT INTO valores_obtenidos (indicador_id, gestion_id, mes_id, valor_obtenido)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE valor_obtenido = VALUES(valor_obtenido)
        """,
        (indicador_id, gestion_id, mes_id, valor),
    )


def get_metas_valores(indicador_id, gestion_id, periodo_id=None):
    params = [indicador_id, gestion_id, indicador_id, gestion_id]
    join_periodo = ""
    where_periodo = ""
    if periodo_id:
        join_periodo = "JOIN periodos p ON p.id = %s"
        where_periodo = "AND m.numero_mes BETWEEN mi.numero_mes AND mf.numero_mes"
        params = [periodo_id, indicador_id, gestion_id, indicador_id, gestion_id]
    return fetch_all(
        f"""
        SELECT m.id AS mes_id, m.nombre AS mes, m.numero_mes,
               mm.meta_mensual, vo.valor_obtenido
        FROM meses m
        {join_periodo}
        {"JOIN meses mi ON p.mes_inicio_id = mi.id JOIN meses mf ON p.mes_fin_id = mf.id" if periodo_id else ""}
        LEFT JOIN metas_mensuales mm
            ON mm.mes_id = m.id
            AND mm.indicador_id = %s
            AND mm.gestion_id = %s
        LEFT JOIN valores_obtenidos vo
            ON vo.mes_id = m.id
            AND vo.indicador_id = %s
            AND vo.gestion_id = %s
        WHERE 1=1 {where_periodo}
        ORDER BY m.numero_mes
        """,
        tuple(params),
    )


def save_avance(indicador_id, periodo_id, tipo_avance, resultado):
    execute(
        """
        INSERT INTO avances (indicador_id, periodo_id, tipo_avance, resultado)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE resultado = VALUES(resultado)
        """,
        (indicador_id, periodo_id, tipo_avance, resultado),
    )


def calcular_avance_tipo_1(gestion_id, periodo_id):
    periodo = fetch_one(
        """
        SELECT p.id, p.gestion_id, p.nombre, p.mes_fin_id, m.nombre AS mes_fin_nombre
        FROM periodos p
        JOIN meses m ON p.mes_fin_id = m.id
        WHERE p.id = %s AND p.gestion_id = %s
        """,
        (periodo_id, gestion_id),
    )
    if not periodo:
        return {
            "calculados": 0,
            "omitidos": 0,
            "periodo": None,
            "mes": None,
        }

    filas = fetch_all(
        """
        SELECT i.id, i.codigo, i.nombre_indicador,
               mm.meta_mensual, vo.valor_obtenido
        FROM indicadores i
        LEFT JOIN metas_mensuales mm
            ON mm.indicador_id = i.id
            AND mm.gestion_id = %s
            AND mm.mes_id = %s
        LEFT JOIN valores_obtenidos vo
            ON vo.indicador_id = i.id
            AND vo.gestion_id = %s
            AND vo.mes_id = %s
        WHERE i.estado = 1
        ORDER BY i.codigo
        """,
        (gestion_id, periodo["mes_fin_id"], gestion_id, periodo["mes_fin_id"]),
    )

    calculados = 0
    omitidos = 0
    for fila in filas:
        meta = fila["meta_mensual"]
        valor = fila["valor_obtenido"]
        if meta in (None, 0) or valor is None:
            omitidos += 1
            continue

        resultado = float(valor) / float(meta) * 100
        save_avance(fila["id"], periodo_id, "TIPO_1", resultado)
        calculados += 1

    return {
        "calculados": calculados,
        "omitidos": omitidos,
        "periodo": periodo["nombre"],
        "mes": periodo["mes_fin_nombre"],
    }


def get_panel_seguimiento(gestion_id, periodo_id):
    return fetch_all(
        """
        SELECT i.id AS indicador_id, i.codigo, i.nombre_indicador,
               g.nombre AS gestion,
               p.id AS periodo_id, p.nombre AS periodo,
               mf.numero_mes AS mes_fin,
               mf.nombre AS mes_fin_nombre,
               mm.meta_mensual AS meta_cierre,
               ma.meta_anual,
               vo.valor_obtenido AS valor_cierre,
               a.resultado AS avance_tipo_1
        FROM indicadores i
        JOIN periodos p ON p.id = %s AND p.gestion_id = %s
        JOIN gestiones g ON p.gestion_id = g.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        LEFT JOIN metas_mensuales mm
            ON mm.indicador_id = i.id
            AND mm.gestion_id = p.gestion_id
            AND mm.mes_id = p.mes_fin_id
        LEFT JOIN metas_anuales ma
            ON ma.indicador_id = i.id
            AND ma.gestion_id = p.gestion_id
        LEFT JOIN valores_obtenidos vo
            ON vo.indicador_id = i.id
            AND vo.gestion_id = p.gestion_id
            AND vo.mes_id = p.mes_fin_id
        LEFT JOIN avances a
            ON a.indicador_id = i.id
            AND a.periodo_id = p.id
            AND a.tipo_avance = 'TIPO_1'
        WHERE i.estado = 1
        ORDER BY i.codigo
        """,
        (periodo_id, gestion_id),
    )


def get_panel_evolucion(gestion_id, periodo_id):
    return fetch_all(
        """
        SELECT m.nombre AS mes,
               ROUND(AVG(mm.meta_mensual), 2) AS meta_promedio,
               ROUND(AVG(ma.meta_anual), 2) AS meta_anual_promedio,
               ROUND(AVG(vo.valor_obtenido), 2) AS valor_promedio
        FROM meses m
        JOIN periodos p ON p.id = %s AND p.gestion_id = %s
        JOIN meses mi ON p.mes_inicio_id = mi.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        JOIN indicadores i ON i.estado = 1
        LEFT JOIN metas_mensuales mm
            ON mm.indicador_id = i.id
            AND mm.gestion_id = p.gestion_id
            AND mm.mes_id = m.id
        LEFT JOIN metas_anuales ma
            ON ma.indicador_id = i.id
            AND ma.gestion_id = p.gestion_id
        LEFT JOIN valores_obtenidos vo
            ON vo.indicador_id = i.id
            AND vo.gestion_id = p.gestion_id
            AND vo.mes_id = m.id
        WHERE m.numero_mes BETWEEN mi.numero_mes AND mf.numero_mes
        GROUP BY m.id, m.nombre, m.numero_mes
        ORDER BY m.numero_mes
        """,
        (periodo_id, gestion_id),
    )


def get_avances(gestion_id=None, indicador_id=None):
    filters = []
    params = []
    if gestion_id:
        filters.append("p.gestion_id = %s")
        params.append(gestion_id)
    if indicador_id:
        filters.append("a.indicador_id = %s")
        params.append(indicador_id)
    where = "WHERE " + " AND ".join(filters) if filters else ""
    return fetch_all(
        f"""
        SELECT a.id, a.tipo_avance, a.resultado,
               i.codigo, i.nombre_indicador,
               p.nombre AS periodo, g.nombre AS gestion,
               mf.numero_mes AS mes_fin
        FROM avances a
        JOIN indicadores i ON a.indicador_id = i.id
        JOIN periodos p ON a.periodo_id = p.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        JOIN gestiones g ON p.gestion_id = g.id
        {where}
        ORDER BY g.nombre, p.mes_inicio_id, i.codigo, a.tipo_avance
        """,
        tuple(params),
    )
