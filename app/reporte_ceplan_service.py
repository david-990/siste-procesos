"""
Servicio para generar reportes según formato CEPLAN.
Incluye funciones para organizar datos de indicadores por período,
calcular semaforización y generar alertas.
"""

from decimal import Decimal
from app.db import fetch_all, fetch_one


def get_avance_tipo1_data(gestion_id, periodo_id):
    """
    Obtiene datos de avance Tipo 1 organizados por mes para presentación CEPLAN.
    
    Retorna un diccionario con:
    - periodo_info: información del período
    - objetivos: lista de objetivos con sus acciones e indicadores
    - meses: lista ordenada de meses del período
    - semaforización: conteo de elementos por rango de avance
    - alertas: lista de elementos en rango crítico (<75%)
    """
    
    # Obtener información del período
    periodo = fetch_one(
        """
        SELECT p.id, p.gestion_id, p.nombre, 
               p.mes_inicio_id, p.mes_fin_id,
               mi.nombre AS mes_inicio_nombre,
               mf.nombre AS mes_fin_nombre,
               mi.numero_mes AS num_mes_inicio,
               mf.numero_mes AS num_mes_fin
        FROM periodos p
        JOIN meses mi ON p.mes_inicio_id = mi.id
        JOIN meses mf ON p.mes_fin_id = mf.id
        WHERE p.id = %s AND p.gestion_id = %s
        """,
        (periodo_id, gestion_id)
    )
    
    if not periodo:
        return None
    
    # Obtener lista de meses del período
    meses = fetch_all(
        """
        SELECT id, nombre, numero_mes
        FROM meses
        WHERE numero_mes BETWEEN %s AND %s
        ORDER BY numero_mes
        """,
        (periodo["num_mes_inicio"], periodo["num_mes_fin"])
    )
    
    # Obtener objetivos con sus acciones e indicadores
    objetivos = fetch_all(
        """
        SELECT DISTINCT 
               oe.id, oe.nombre
        FROM objetivos_estrategicos oe
        JOIN acciones_estrategicas ae ON ae.objetivo_estrategico_id = oe.id
        JOIN indicadores i ON i.accion_estrategica_id = ae.id
        WHERE i.estado = 1
        ORDER BY oe.id
        """
    )
    
    # Estructura de datos jerárquica
    estructura = []
    conteo_semaforización = {
        'objetivos': {'rojo': 0, 'amarillo': 0, 'verde': 0, 'gris': 0},
        'acciones': {'rojo': 0, 'amarillo': 0, 'verde': 0, 'gris': 0},
        'indicadores': {'rojo': 0, 'amarillo': 0, 'verde': 0, 'gris': 0},
    }
    alertas = []
    
    for objetivo in objetivos:
        objetivo_id = objetivo['id']
        objetivo_nombre = objetivo['nombre']
        
        # Obtener acciones de este objetivo
        acciones = fetch_all(
            """
            SELECT ae.id, ae.nombre
            FROM acciones_estrategicas ae
            WHERE ae.objetivo_estrategico_id = %s
            """,
            (objetivo_id,)
        )
        
        acciones_data = []
        avances_objetivo = []
        
        for accion in acciones:
            accion_id = accion['id']
            accion_nombre = accion['nombre']
            
            # Obtener indicadores de esta acción
            indicadores = fetch_all(
                """
                SELECT i.id, i.codigo, i.nombre_indicador, i.prioridad, 
                       i.sentido_esperado, i.tipo_agregacion,
                       a.resultado AS avance_final
                FROM indicadores i
                LEFT JOIN avances a
                    ON a.indicador_id = i.id
                    AND a.periodo_id = %s
                    AND a.tipo_avance = %s
                WHERE i.accion_estrategica_id = %s AND i.estado = 1
                ORDER BY i.codigo
                """,
                (periodo_id, 'TIPO_1', accion_id)
            )
            
            indicadores_data = []
            avances_accion = []
            
            for indicador in indicadores:
                indicador_id = indicador['id']
                
                # Obtener línea base
                linea_base = fetch_one(
                    """
                    SELECT linea_base
                    FROM lineas_base
                    WHERE indicador_id = %s AND gestion_id = %s
                    """,
                    (indicador_id, gestion_id)
                )
                
                # Obtener meta anual
                meta_anual = fetch_one(
                    """
                    SELECT meta_anual
                    FROM metas_anuales
                    WHERE indicador_id = %s AND gestion_id = %s
                    """,
                    (indicador_id, gestion_id)
                )
                
                # Obtener metas y valores mensuales
                metas_valores = fetch_all(
                    """
                    SELECT m.id, m.nombre, m.numero_mes,
                           mm.meta_mensual, vo.valor_obtenido
                    FROM meses m
                    LEFT JOIN metas_mensuales mm 
                        ON mm.mes_id = m.id 
                        AND mm.indicador_id = %s 
                        AND mm.gestion_id = %s
                    LEFT JOIN valores_obtenidos vo 
                        ON vo.mes_id = m.id 
                        AND vo.indicador_id = %s 
                        AND vo.gestion_id = %s
                    WHERE m.numero_mes BETWEEN %s AND %s
                    ORDER BY m.numero_mes
                    """,
                    (indicador_id, gestion_id, indicador_id, gestion_id, 
                     periodo["num_mes_inicio"], periodo["num_mes_fin"])
                )
                
                # Usar el avance final reportado en la tabla avances
                avance_final = float(indicador['avance_final']) if indicador['avance_final'] is not None else None
                
                # Determinar semáforo
                semaforo = _determinar_semaforo(avance_final)
                if semaforo['color'] in conteo_semaforización['indicadores']:
                    conteo_semaforización['indicadores'][semaforo['color']] += 1
                
                # Agregar a alertas si es crítico
                if avance_final is not None and avance_final < 75:
                    alertas.append({
                        'tipo': 'indicador',
                        'nombre': f"{indicador['codigo']} - {indicador['nombre_indicador']}",
                        'avance': round(avance_final, 2),
                        'objetivo_id': objetivo_id,
                        'accion_id': accion_id,
                        'indicador_id': indicador_id
                    })
                
                avances_accion.append(avance_final)
                
                # Formatear datos para la vista
                meses_data = []
                for mes in metas_valores:
                    meses_data.append({
                        'mes_id': mes['id'],
                        'mes_nombre': mes['nombre'],
                        'meta_mensual': float(mes['meta_mensual']) if mes['meta_mensual'] else None,
                        'valor_obtenido': float(mes['valor_obtenido']) if mes['valor_obtenido'] else None,
                    })
                
                indicadores_data.append({
                    'id': indicador_id,
                    'codigo': indicador['codigo'],
                    'nombre': indicador['nombre_indicador'],
                    'prioridad': indicador['prioridad'],
                    'sentido_esperado': indicador['sentido_esperado'],
                    'linea_base': {
                        'valor': float(linea_base['linea_base']) if linea_base else None,
                        'gestion': gestion_id
                    },
                    'meses': meses_data,
                    'avance_final': round(avance_final, 2) if avance_final is not None else None,
                    'semaforo': semaforo
                })
            
            # Calcular avance de la acción (promedio de sus indicadores)
            avance_accion = _promediar(avances_accion)
            semaforo_accion = _determinar_semaforo(avance_accion)
            if semaforo_accion['color'] in conteo_semaforización['acciones']:
                conteo_semaforización['acciones'][semaforo_accion['color']] += 1
            
            if avance_accion is not None and avance_accion < 75:
                alertas.append({
                    'tipo': 'accion',
                    'nombre': accion_nombre,
                    'avance': round(avance_accion, 2),
                    'objetivo_id': objetivo_id,
                    'accion_id': accion_id
                })
            
            avances_objetivo.append(avance_accion if avance_accion else 0)
            
            acciones_data.append({
                'id': accion_id,
                'nombre': accion_nombre,
                'indicadores': indicadores_data,
                'avance': round(avance_accion, 2) if avance_accion is not None else None,
                'semaforo': semaforo_accion
            })
        
        # Calcular avance del objetivo (promedio de sus acciones)
        avance_objetivo = _promediar(avances_objetivo)
        semaforo_objetivo = _determinar_semaforo(avance_objetivo)
        if semaforo_objetivo['color'] in conteo_semaforización['objetivos']:
            conteo_semaforización['objetivos'][semaforo_objetivo['color']] += 1
        
        if avance_objetivo is not None and avance_objetivo < 75:
            alertas.append({
                'tipo': 'objetivo',
                'nombre': objetivo_nombre,
                'avance': round(avance_objetivo, 2),
                'objetivo_id': objetivo_id
            })
        
        estructura.append({
            'id': objetivo_id,
            'nombre': objetivo_nombre,
            'acciones': acciones_data,
            'avance': round(avance_objetivo, 2) if avance_objetivo is not None else None,
            'semaforo': semaforo_objetivo
        })
    
    return {
        'periodo_info': {
            'id': periodo['id'],
            'nombre': periodo['nombre'],
            'mes_inicio': periodo['mes_inicio_nombre'],
            'mes_fin': periodo['mes_fin_nombre'],
            'gestion_id': gestion_id
        },
        'meses': meses,
        'objetivos': estructura,
        'semaforización': conteo_semaforización,
        'alertas': sorted(alertas, key=lambda x: x['avance'])
    }


def _calcular_avance_indicador(mesas_valores, tipo_agregacion):
    """
    Calcula el avance final de un indicador según su tipo de agregación.
    
    - NO_AGREGABLE: usa el valor del último mes del período
    - AGREGABLE: suma todos los valores mensuales
    """
    if not mesas_valores:
        return None
    
    # Filtrar solo los meses con valor obtenido
    valores_con_datos = [
        float(mv['valor_obtenido']) 
        for mv in mesas_valores 
        if mv['valor_obtenido'] is not None
    ]
    
    if not valores_con_datos:
        return None
    
    if tipo_agregacion == 'NO_AGREGABLE':
        # Para indicadores NO_AGREGABLE, usar el valor del último mes
        return valores_con_datos[-1] if valores_con_datos else None
    else:
        # Para indicadores AGREGABLE, sumar todos los valores
        return sum(valores_con_datos)


def _promediar(avances):
    validos = [a for a in avances if a is not None]
    return (sum(validos) / len(validos)) if validos else None


def _determinar_semaforo(avance):
    """
    Determina el color del semáforo según el rango de avance.
    
    - Rojo: 0-75%
    - Amarillo: 75-95%
    - Verde: 95-100%
    """
    if avance is None:
        return {'color': 'gris', 'nombre': 'Sin dato', 'clase': 'bg-slate-100 text-slate-600'}
    
    avance_float = float(avance)
    
    if avance_float < 75:
        return {
            'color': 'rojo',
            'nombre': 'Crítico',
            'clase': 'bg-red-100 text-red-700',
            'hex': '#ef4444'
        }
    elif avance_float < 95:
        return {
            'color': 'amarillo',
            'nombre': 'En seguimiento',
            'clase': 'bg-amber-100 text-amber-700',
            'hex': '#f59e0b'
        }
    else:
        return {
            'color': 'verde',
            'nombre': 'Concluido',
            'clase': 'bg-emerald-100 text-emerald-700',
            'hex': '#10b981'
        }
