from datetime import datetime

import mysql.connector

from app.db import execute, execute_many, fetch_all, fetch_one


def get_user_by_id(user_id):
    return fetch_one(
        "SELECT id, username, nombre, role, is_active FROM users WHERE id = %s",
        (user_id,),
    )


def get_user_by_username(username):
    return fetch_one(
        """
        SELECT id, username, password_hash, nombre, role, is_active
        FROM users
        WHERE username = %s AND is_active = 1
        """,
        (username,),
    )


def update_user_password(user_id, password_hash):
    execute(
        """
        UPDATE users
        SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (password_hash, user_id),
    )


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
    where = "WHERE i.estado = 1" if not include_inactive else ""
    return fetch_all(
        f"""
        SELECT i.id, i.accion_estrategica_id, i.codigo, i.nombre_indicador, i.prioridad, i.sentido_esperado,
               i.formula, i.tipo_agregacion, i.estado, ae.nombre AS accion_nombre
        FROM indicadores i
        JOIN acciones_estrategicas ae ON i.accion_estrategica_id = ae.id
        {where}
        ORDER BY i.codigo
        """
    )


def get_indicador(indicador_id):
    return fetch_one("SELECT * FROM indicadores WHERE id = %s", (indicador_id,))


def save_indicador(data, indicador_id=None):
    params = (
        data["accion_estrategica_id"],
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
            SET accion_estrategica_id=%s, codigo=%s, nombre_indicador=%s, prioridad=%s,
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
            (accion_estrategica_id, codigo, nombre_indicador, prioridad, sentido_esperado, formula, tipo_agregacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
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
        SELECT ae.id, ae.objetivo_estrategico_id, ae.nombre AS nombre_accion,
               oe.nombre AS objetivo_nombre
        FROM acciones_estrategicas ae
        JOIN objetivos_estrategicos oe ON ae.objetivo_estrategico_id = oe.id
        ORDER BY oe.id, ae.id
        """
    )


def save_accion(data, accion_id=None):
    params = (
        data["objetivo_estrategico_id"],
        data["nombre"],
    )
    if accion_id:
        execute(
            """
            UPDATE acciones_estrategicas
            SET objetivo_estrategico_id=%s, nombre=%s
            WHERE id=%s
            """,
            (*params, accion_id),
        )
        return accion_id
    return execute(
        """
        INSERT INTO acciones_estrategicas (objetivo_estrategico_id, nombre)
        VALUES (%s, %s)
        """,
        params,
    )


def delete_accion(accion_id):
    execute("DELETE FROM acciones_estrategicas WHERE id = %s", (accion_id,))


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


def save_avances(avances):
    if not avances:
        return 0
    return execute_many(
        """
        INSERT INTO avances (indicador_id, periodo_id, tipo_avance, resultado)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE resultado = VALUES(resultado)
        """,
        avances,
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

    avances = []
    omitidos = 0
    for fila in filas:
        meta = fila["meta_mensual"]
        valor = fila["valor_obtenido"]
        if meta in (None, 0) or valor is None:
            omitidos += 1
            continue

        resultado = float(valor) / float(meta) * 100
        avances.append((fila["id"], periodo_id, "TIPO_1", resultado))

    save_avances(avances)
    calculados = len(avances)

    # Recalcular promedio de avance para cada Acción Estratégica
    execute(
        """
        INSERT INTO avances_acciones_estrategicas (accion_estrategica_id, periodo_id, tipo_avance, resultado)
        SELECT i.accion_estrategica_id, %s, 'TIPO_1', AVG(a.resultado)
        FROM avances a
        JOIN indicadores i ON a.indicador_id = i.id
        WHERE a.periodo_id = %s AND a.tipo_avance = 'TIPO_1'
        GROUP BY i.accion_estrategica_id
        ON DUPLICATE KEY UPDATE resultado = VALUES(resultado)
        """,
        (periodo_id, periodo_id)
    )

    # Recalcular promedio de avance para cada Objetivo Estratégico
    execute(
        """
        INSERT INTO avances_objetivos_estrategicos (objetivo_estrategico_id, periodo_id, tipo_avance, resultado)
        SELECT ae.objetivo_estrategico_id, %s, 'TIPO_1', AVG(aa.resultado)
        FROM avances_acciones_estrategicas aa
        JOIN acciones_estrategicas ae ON aa.accion_estrategica_id = ae.id
        WHERE aa.periodo_id = %s AND aa.tipo_avance = 'TIPO_1'
        GROUP BY ae.objetivo_estrategico_id
        ON DUPLICATE KEY UPDATE resultado = VALUES(resultado)
        """,
        (periodo_id, periodo_id)
    )

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
               a.resultado AS avance_tipo_1,
               ae.nombre AS accion_estrategica,
               oe.nombre AS objetivo_estrategico,
               aae.resultado AS avance_accion,
               aoe.resultado AS avance_objetivo
        FROM indicadores i
        JOIN acciones_estrategicas ae ON i.accion_estrategica_id = ae.id
        JOIN objetivos_estrategicos oe ON ae.objetivo_estrategico_id = oe.id
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
        LEFT JOIN avances_acciones_estrategicas aae
            ON aae.accion_estrategica_id = ae.id
            AND aae.periodo_id = p.id
            AND aae.tipo_avance = 'TIPO_1'
        LEFT JOIN avances_objetivos_estrategicos aoe
            ON aoe.objetivo_estrategico_id = oe.id
            AND aoe.periodo_id = p.id
            AND aoe.tipo_avance = 'TIPO_1'
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


def delete_linea_base(linea_base_id):
    execute("DELETE FROM lineas_base WHERE id = %s", (linea_base_id,))


def delete_meta_anual(meta_anual_id):
    execute("DELETE FROM metas_anuales WHERE id = %s", (meta_anual_id,))


def get_objetivos():
    return fetch_all("SELECT id, nombre FROM objetivos_estrategicos ORDER BY id")


def get_objetivo(objetivo_id):
    return fetch_one("SELECT * FROM objetivos_estrategicos WHERE id = %s", (objetivo_id,))


def save_objetivo(data, objetivo_id=None):
    params = (data["nombre"].strip(),)
    if objetivo_id:
        execute("UPDATE objetivos_estrategicos SET nombre=%s WHERE id=%s", (*params, objetivo_id))
        return objetivo_id
    return execute("INSERT INTO objetivos_estrategicos (nombre) VALUES (%s)", params)


def delete_objetivo(objetivo_id):
    execute("DELETE FROM objetivos_estrategicos WHERE id = %s", (objetivo_id,))


def get_avances_acciones(gestion_id):
    return fetch_all(
        """
        SELECT aa.id, aa.resultado, aa.tipo_avance, ae.nombre AS nombre_accion, oe.nombre AS objetivo_nombre,
               p.nombre AS periodo, g.nombre AS gestion, mf.numero_mes AS mes_fin
        FROM avances_acciones_estrategicas aa
        JOIN acciones_estrategicas ae ON aa.accion_estrategica_id = ae.id
        JOIN objetivos_estrategicos oe ON ae.objetivo_estrategico_id = oe.id
        JOIN periodos p ON aa.periodo_id = p.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        JOIN gestiones g ON p.gestion_id = g.id
        WHERE p.gestion_id = %s
        ORDER BY oe.id, ae.id, p.id, aa.tipo_avance
        """,
        (gestion_id,)
    )


def get_avances_objetivos(gestion_id):
    return fetch_all(
        """
        SELECT ao.id, ao.resultado, ao.tipo_avance, oe.nombre AS objetivo_nombre,
               p.nombre AS periodo, g.nombre AS gestion, mf.numero_mes AS mes_fin
        FROM avances_objetivos_estrategicos ao
        JOIN objetivos_estrategicos oe ON ao.objetivo_estrategico_id = oe.id
        JOIN periodos p ON ao.periodo_id = p.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        JOIN gestiones g ON p.gestion_id = g.id
        WHERE p.gestion_id = %s
        ORDER BY oe.id, p.id, ao.tipo_avance
        """,
        (gestion_id,)
    )


def get_procesos():
    return fetch_all(
        """
        SELECT p.id, p.nivel, p.tipo_proceso, p.producto_proceso, p.codigo_proceso, p.nombre_proceso, p.proceso_padre_id,
               padre.nombre_proceso AS nombre_padre, padre.codigo_proceso AS codigo_padre
        FROM procesos p
        LEFT JOIN procesos padre ON p.proceso_padre_id = padre.id
        ORDER BY p.codigo_proceso
        """
    )


def get_proceso(proceso_id):
    return fetch_one("SELECT * FROM procesos WHERE id = %s", (proceso_id,))


def get_proceso_by_codigo(codigo):
    return fetch_one("SELECT * FROM procesos WHERE codigo_proceso = %s", (codigo.strip(),))


def save_proceso(data, proceso_id=None):
    params = (
        int(data["nivel"]),
        data["tipo_proceso"],
        data["producto_proceso"].strip(),
        data["codigo_proceso"].strip(),
        data["nombre_proceso"].strip(),
        data.get("proceso_padre_id"),
    )
    if proceso_id:
        execute(
            """
            UPDATE procesos
            SET nivel=%s, tipo_proceso=%s, producto_proceso=%s, codigo_proceso=%s, nombre_proceso=%s, proceso_padre_id=%s
            WHERE id=%s
            """,
            (*params, proceso_id),
        )
        return proceso_id
    return execute(
        """
        INSERT INTO procesos (nivel, tipo_proceso, producto_proceso, codigo_proceso, nombre_proceso, proceso_padre_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        params,
    )


def delete_proceso(proceso_id):
    execute("DELETE FROM procesos WHERE id = %s", (proceso_id,))


def get_mapa():
    return fetch_one("SELECT * FROM mapa LIMIT 1")


def save_mapa(imagen_filename):
    existing = get_mapa()
    if existing:
        execute("UPDATE mapa SET imagen = %s WHERE id = %s", (imagen_filename, existing["id"]))
        return existing["id"]
    return execute("INSERT INTO mapa (imagen) VALUES (%s)", (imagen_filename,))


def _ensure_ficha_caracterizacion_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS fichas_caracterizacion (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            codigo_proceso VARCHAR(255) NULL,
            nombre_proceso VARCHAR(255) NULL,
            tipo_proceso VARCHAR(255) NULL,
            dueno_proceso VARCHAR(255) NULL,
            objetivo_proceso TEXT NULL,
            objetivo_estrategico TEXT NULL,
            proveedor_entrada TEXT NULL,
            elementos_entrada TEXT NULL,
            producto TEXT NULL,
            receptor_producto TEXT NULL,
            actividades_proceso_imagen VARCHAR(255) NULL,
            riesgos TEXT NULL,
            registros TEXT NULL,
            elaborado_por VARCHAR(255) NULL,
            revisado_por VARCHAR(255) NULL,
            aprobado_por VARCHAR(255) NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )


def get_fichas_caracterizacion():
    _ensure_ficha_caracterizacion_table()
    return fetch_all(
        """
        SELECT id, codigo_proceso, nombre_proceso, tipo_proceso, dueno_proceso,
               objetivo_proceso, objetivo_estrategico, proveedor_entrada,
               elementos_entrada, producto, receptor_producto,
               actividades_proceso_imagen, riesgos, registros,
               elaborado_por, revisado_por, aprobado_por, created_at
        FROM fichas_caracterizacion
        ORDER BY id DESC
        """
    )


def get_ficha_caracterizacion(ficha_id):
    _ensure_ficha_caracterizacion_table()
    return fetch_one(
        """
        SELECT id, codigo_proceso, nombre_proceso, tipo_proceso, dueno_proceso,
               objetivo_proceso, objetivo_estrategico, proveedor_entrada,
               elementos_entrada, producto, receptor_producto,
               actividades_proceso_imagen, riesgos, registros,
               elaborado_por, revisado_por, aprobado_por, created_at
        FROM fichas_caracterizacion
        WHERE id = %s
        """,
        (ficha_id,),
    )


def save_ficha_caracterizacion(data, ficha_id=None):
    _ensure_ficha_caracterizacion_table()
    params = (
        data.get("codigo_proceso", "").strip(),
        data.get("nombre_proceso", "").strip(),
        data.get("tipo_proceso") or None,
        data.get("dueno_proceso") or None,
        data.get("objetivo_proceso") or None,
        data.get("objetivo_estrategico") or None,
        data.get("proveedor_entrada") or None,
        data.get("elementos_entrada") or None,
        data.get("producto") or None,
        data.get("receptor_producto") or None,
        data.get("actividades_proceso_imagen") or None,
        data.get("riesgos") or None,
        data.get("registros") or None,
        data.get("elaborado_por") or None,
        data.get("revisado_por") or None,
        data.get("aprobado_por") or None,
    )
    if ficha_id:
        execute(
            """
            UPDATE fichas_caracterizacion
            SET codigo_proceso=%s, nombre_proceso=%s, tipo_proceso=%s, dueno_proceso=%s,
                objetivo_proceso=%s, objetivo_estrategico=%s, proveedor_entrada=%s,
                elementos_entrada=%s, producto=%s, receptor_producto=%s,
                actividades_proceso_imagen=%s, riesgos=%s, registros=%s,
                elaborado_por=%s, revisado_por=%s, aprobado_por=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (*params, ficha_id),
        )
        return ficha_id
    return execute(
        """
        INSERT INTO fichas_caracterizacion (
            codigo_proceso, nombre_proceso, tipo_proceso, dueno_proceso,
            objetivo_proceso, objetivo_estrategico, proveedor_entrada,
            elementos_entrada, producto, receptor_producto,
            actividades_proceso_imagen, riesgos, registros,
            elaborado_por, revisado_por, aprobado_por
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        params,
    )

def delete_ficha_caracterizacion(ficha_id):
    execute("DELETE FROM fichas_caracterizacion WHERE id = %s", (ficha_id,))


def _ensure_pendientes_table():
    """Crea la tabla archivos_pendientes_eliminar si no existe."""
    execute(
        """
        CREATE TABLE IF NOT EXISTS archivos_pendientes_eliminar (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            ruta_archivo VARCHAR(1024) NOT NULL,
            intentos TINYINT UNSIGNED NOT NULL DEFAULT 0,
            ultimo_error TEXT NULL,
            proximo_intento_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            procesando_at TIMESTAMP NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_proximo_intento (proximo_intento_at, procesando_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )


def enqueue_pendiente(ruta_archivo):
    """Encola una ruta de archivo para eliminación asíncrona."""
    if not ruta_archivo:
        return
    _ensure_pendientes_table()
    execute(
        """
        INSERT IGNORE INTO archivos_pendientes_eliminar (ruta_archivo)
        VALUES (%s)
        """,
        (ruta_archivo,),
    )


def claim_pendientes(limit=20):
    """
    Reclama hasta `limit` trabajos pendientes que estén listos para procesar.
    Retorna una lista de dicts con id, ruta_archivo, intentos.
    """
    _ensure_pendientes_table()
    return fetch_all(
        """
        SELECT id, ruta_archivo, intentos
        FROM archivos_pendientes_eliminar
        WHERE proximo_intento_at <= NOW()
          AND (procesando_at IS NULL OR procesando_at < NOW() - INTERVAL 10 MINUTE)
        ORDER BY proximo_intento_at, id
        LIMIT %s
        """,
        (limit,),
    )


def mark_pendiente_procesando(pendiente_id):
    """Marca un pendiente como 'en proceso'."""
    execute(
        "UPDATE archivos_pendientes_eliminar SET procesando_at = NOW() WHERE id = %s",
        (pendiente_id,),
    )


def resolve_pendiente(pendiente_id):
    """Elimina un pendiente de la cola (borrado exitoso)."""
    execute(
        "DELETE FROM archivos_pendientes_eliminar WHERE id = %s",
        (pendiente_id,),
    )


def fail_pendiente(pendiente_id, error_msg):
    """
    Incrementa intentos, guarda el error, y programa el próximo reintento
    con backoff exponencial: min(60 × 2^intentos, 3600) segundos.
    """
    execute(
        """
        UPDATE archivos_pendientes_eliminar
        SET intentos = intentos + 1,
            ultimo_error = %s,
            proximo_intento_at = DATE_ADD(NOW(), INTERVAL LEAST(60 * POW(2, intentos), 3600) SECOND),
            procesando_at = NULL
        WHERE id = %s
        """,
        (error_msg, pendiente_id),
    )


def _ensure_ficha_indicadores_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS fichas_indicadores (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            ficha_caracterizacion_id INT UNSIGNED NOT NULL,
            proceso VARCHAR(255) NOT NULL,
            producto VARCHAR(255) NOT NULL,
            nombre_indicador VARCHAR(255) NOT NULL,
            tipo_indicador VARCHAR(100) NOT NULL,
            justificacion TEXT NULL,
            responsable VARCHAR(255) NOT NULL,
            metodo_calculo TEXT NULL,
            sentido_esperado VARCHAR(100) NOT NULL,
            unidad_medida VARCHAR(100) NOT NULL,
            frecuencia VARCHAR(100) NOT NULL,
            fuente_datos VARCHAR(255) NOT NULL,
            valor_enero VARCHAR(50) NULL,
            valor_febrero VARCHAR(50) NULL,
            valor_marzo VARCHAR(50) NULL,
            valor_abril VARCHAR(50) NULL,
            valor_mayo VARCHAR(50) NULL,
            valor_junio VARCHAR(50) NULL,
            elaborado_por VARCHAR(150) NULL,
            revisado_por VARCHAR(150) NULL,
            aprobado_por VARCHAR(150) NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (ficha_caracterizacion_id) REFERENCES fichas_caracterizacion(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )


def get_fichas_indicadores():
    _ensure_ficha_indicadores_table()
    return fetch_all(
        """
        SELECT fi.id, fi.ficha_caracterizacion_id, fi.proceso, fi.producto,
               fi.nombre_indicador, fi.tipo_indicador, fi.justificacion,
               fi.responsable, fi.metodo_calculo, fi.sentido_esperado,
               fi.unidad_medida, fi.frecuencia, fi.fuente_datos,
               fi.valor_enero, fi.valor_febrero, fi.valor_marzo, fi.valor_abril,
               fi.valor_mayo, fi.valor_junio,
               fi.elaborado_por, fi.revisado_por, fi.aprobado_por, fi.created_at,
               fc.nombre_proceso AS ficha_caracterizacion_nombre
        FROM fichas_indicadores fi
        LEFT JOIN fichas_caracterizacion fc ON fi.ficha_caracterizacion_id = fc.id
        ORDER BY fi.id DESC
        """
    )


def get_ficha_indicador(ficha_id):
    _ensure_ficha_indicadores_table()
    return fetch_one(
        """
        SELECT fi.id, fi.ficha_caracterizacion_id, fi.proceso, fi.producto,
               fi.nombre_indicador, fi.tipo_indicador, fi.justificacion,
               fi.responsable, fi.metodo_calculo, fi.sentido_esperado,
               fi.unidad_medida, fi.frecuencia, fi.fuente_datos,
               fi.valor_enero, fi.valor_febrero, fi.valor_marzo, fi.valor_abril,
               fi.valor_mayo, fi.valor_junio,
               fi.elaborado_por, fi.revisado_por, fi.aprobado_por, fi.created_at,
               fc.nombre_proceso AS ficha_caracterizacion_nombre
        FROM fichas_indicadores fi
        LEFT JOIN fichas_caracterizacion fc ON fi.ficha_caracterizacion_id = fc.id
        WHERE fi.id = %s
        """,
        (ficha_id,),
    )


def save_ficha_indicador(data, ficha_id=None):
    _ensure_ficha_indicadores_table()
    params = (
        data.get("ficha_caracterizacion_id"),
        data.get("proceso"),
        data.get("producto"),
        data.get("nombre_indicador"),
        data.get("tipo_indicador"),
        data.get("justificacion"),
        data.get("responsable"),
        data.get("metodo_calculo"),
        data.get("sentido_esperado"),
        data.get("unidad_medida"),
        data.get("frecuencia"),
        data.get("fuente_datos"),
        data.get("valor_enero"),
        data.get("valor_febrero"),
        data.get("valor_marzo"),
        data.get("valor_abril"),
        data.get("valor_mayo"),
        data.get("valor_junio"),
        data.get("elaborado_por"),
        data.get("revisado_por"),
        data.get("aprobado_por"),
    )
    if ficha_id:
        execute(
            """
            UPDATE fichas_indicadores
            SET ficha_caracterizacion_id=%s, proceso=%s, producto=%s, nombre_indicador=%s,
                tipo_indicador=%s, justificacion=%s, responsable=%s, metodo_calculo=%s,
                sentido_esperado=%s, unidad_medida=%s, frecuencia=%s, fuente_datos=%s,
                valor_enero=%s, valor_febrero=%s, valor_marzo=%s, valor_abril=%s,
                valor_mayo=%s, valor_junio=%s, elaborado_por=%s, revisado_por=%s,
                aprobado_por=%s, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (*params, ficha_id),
        )
        return ficha_id
    return execute(
        """
        INSERT INTO fichas_indicadores (
            ficha_caracterizacion_id, proceso, producto, nombre_indicador,
            tipo_indicador, justificacion, responsable, metodo_calculo,
            sentido_esperado, unidad_medida, frecuencia, fuente_datos,
            valor_enero, valor_febrero, valor_marzo, valor_abril,
            valor_mayo, valor_junio, elaborado_por, revisado_por, aprobado_por
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        params,
    )


def delete_ficha_indicador(ficha_id):
    execute("DELETE FROM fichas_indicadores WHERE id = %s", (ficha_id,))


def get_resumen_ia(gestion_id, periodo_id):
    row = fetch_one(
        "SELECT resumen FROM resumenes_ia WHERE gestion_id = %s AND periodo_id = %s",
        (gestion_id, periodo_id),
    )
    return row["resumen"] if row else None


def _ensure_kurt_lewin_column():
    execute("ALTER TABLE resumenes_ia ADD COLUMN kurt_lewin text NULL")


def get_kurt_lewin_ia(gestion_id, periodo_id):
    try:
        row = fetch_one(
            "SELECT kurt_lewin FROM resumenes_ia WHERE gestion_id = %s AND periodo_id = %s",
            (gestion_id, periodo_id),
        )
    except mysql.connector.Error as error:
        if error.errno != 1054:
            raise
        _ensure_kurt_lewin_column()
        return None
    return row["kurt_lewin"] if row else None


def save_resumen_ia(gestion_id, periodo_id, resumen):
    execute(
        """
        INSERT INTO resumenes_ia (gestion_id, periodo_id, resumen)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE resumen = VALUES(resumen)
        """,
        (gestion_id, periodo_id, resumen),
    )


def save_kurt_lewin_ia(gestion_id, periodo_id, kurt_lewin):
    try:
        execute(
            """
            INSERT INTO resumenes_ia (gestion_id, periodo_id, resumen, kurt_lewin)
            VALUES (%s, %s, '', %s)
            ON DUPLICATE KEY UPDATE kurt_lewin = VALUES(kurt_lewin)
            """,
            (gestion_id, periodo_id, kurt_lewin),
        )
    except mysql.connector.Error as error:
        if error.errno != 1054:
            raise
        _ensure_kurt_lewin_column()
        execute(
            """
            INSERT INTO resumenes_ia (gestion_id, periodo_id, resumen, kurt_lewin)
            VALUES (%s, %s, '', %s)
            ON DUPLICATE KEY UPDATE kurt_lewin = VALUES(kurt_lewin)
            """,
            (gestion_id, periodo_id, kurt_lewin),
        )


def get_indicadores_sin_procesos():
    return fetch_all(
        """
        SELECT i.id, i.codigo, i.nombre_indicador
        FROM indicadores i
        LEFT JOIN indicadores_procesos ip ON i.id = ip.indicador_id
        WHERE ip.indicador_id IS NULL AND i.estado = 1
        ORDER BY i.codigo
        """
    )


def link_indicador_proceso(indicador_id, proceso_id):
    try:
        execute(
            "INSERT INTO indicadores_procesos (indicador_id, proceso_id) VALUES (%s, %s)",
            (indicador_id, proceso_id),
        )
        return True
    except mysql.connector.Error:
        return False


def get_vinculaciones_completas():
    return fetch_all(
        """
        SELECT i.codigo AS codigo_indicador, i.nombre_indicador, p.codigo_proceso, p.nombre_proceso
        FROM indicadores_procesos ip
        JOIN indicadores i ON ip.indicador_id = i.id
        JOIN procesos p ON ip.proceso_id = p.id
        ORDER BY p.codigo_proceso, i.codigo
        """
    )


def get_procesos_by_indicador(indicador_id):
    return fetch_all(
        """
        SELECT p.id, p.codigo_proceso, p.nombre_proceso, p.tipo_proceso
        FROM procesos p
        JOIN indicadores_procesos ip ON p.id = ip.proceso_id
        WHERE ip.indicador_id = %s
        ORDER BY p.codigo_proceso
        """,
        (indicador_id,)
    )


def get_indicadores_con_procesos():
    return fetch_all(
        """
        SELECT DISTINCT i.id, i.codigo, i.nombre_indicador
        FROM indicadores i
        JOIN indicadores_procesos ip ON i.id = ip.indicador_id
        WHERE i.estado = 1
        ORDER BY i.codigo
        """
    )


def save_indicador_procesos(indicador_id, proceso_ids):
    execute("DELETE FROM indicadores_procesos WHERE indicador_id = %s", (indicador_id,))
    if proceso_ids:
        params = [(indicador_id, int(pid)) for pid in proceso_ids]
        execute_many(
            "INSERT INTO indicadores_procesos (indicador_id, proceso_id) VALUES (%s, %s)",
            params
        )
