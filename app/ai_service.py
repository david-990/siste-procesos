import json
import logging

from app.providers import get_provider

logger = logging.getLogger(__name__)
_ai = get_provider()

def generar_resumen_panel(gestion_nombre, periodo_nombre, total_indicadores, evaluados, avance_acciones, avance_objetivos, conteo_estados, seguimiento):
    """
    Genera un análisis narrativo del panel de control utilizando IA.
    """
    # Formatear la lista de indicadores para el prompt
    indicadores_str = ""
    for f in seguimiento:
        avance_str = f"{f['avance_tipo_1']:.2f}%" if f['avance_tipo_1'] is not None else "Sin dato"
        indicadores_str += f"- {f['codigo']}: {f['nombre_indicador']} | Avance: {avance_str} | Estado: {f['estado']['nombre']}\n"

    prompt = f"""Eres un analista experto en gestión pública y monitoreo de procesos de gobierno digital.
Analiza la siguiente información de desempeño institucional del panel de control para el periodo {periodo_nombre} de la gestión {gestion_nombre}:

RESUMEN GENERAL:
- Total de Indicadores: {total_indicadores} (Evaluados: {evaluados})
- Avance promedio de Acciones Estratégicas: {f"{avance_acciones:.2f}%" if avance_acciones is not None else "N/A"}
- Avance promedio de Objetivos Estratégicos (Progreso del periodo): {f"{avance_objetivos:.2f}%" if avance_objetivos is not None else "N/A"}
- Distribución de estados de los indicadores:
  * Concluido (>= 95%): {conteo_estados['Concluido']}
  * En seguimiento (75% - 95%): {conteo_estados['En seguimiento']}
  * Crítico (< 75%): {conteo_estados['Critico']}
  * Sin dato: {conteo_estados['Sin dato']}

DETALLE DE INDICADORES:
{indicadores_str}

Instrucciones para tu respuesta:
1. Escribe el reporte usando formato Markdown limpio. Utiliza títulos y tablas de forma obligatoria.
2. Comienza con una sección corta de **Evaluación General** del periodo (un párrafo corto).
3. Luego, crea la sección **Detalle de Indicadores** y presenta los indicadores en tablas Markdown agrupadas por su estado:
   - Para Concluidos y En Seguimiento, usa las columnas: `| Código | Indicador | Avance tipo 1 obtenido |`.
   - Para Críticos, usa las columnas: `| Código | Indicador | Avance tipo 1 obtenido | Prioridad | Alerta/Acción sugerida |`.
4. **IMPORTANTE: Aplica colores usando etiquetas HTML integradas en la tabla:**
   - En la columna de **Avance tipo 1 obtenido**, envuelve los porcentajes con estos badges según el estado:
     * Para Concluidos (Avance ≥ 95%): `<span class="inline-flex rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">XX.XX%</span>` (reemplaza XX.XX por el valor real).
     * Para En Seguimiento (Avance entre 75% y 95%): `<span class="inline-flex rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-semibold text-amber-700">XX.XX%</span>` (reemplaza XX.XX por el valor real).
     * Para Críticos (Avance < 75% o Sin dato): `<span class="inline-flex rounded-full bg-red-50 border border-red-200 px-2.5 py-0.5 text-xs font-semibold text-red-700">XX.XX%</span>` (reemplaza XX.XX por el valor real o "Sin dato").
   - En la columna de **Prioridad** (para los Críticos), envuelve el nivel de prioridad con estos colores:
     * Prioridad 1: `<span class="text-red-600 font-bold">Alta</span>`
     * Prioridad 2: `<span class="text-amber-600 font-bold">Media</span>`
     * Prioridad 3: `<span class="text-slate-500 font-medium">Baja</span>`
5. Si una categoría de estado no contiene indicadores, escribe "No se registran indicadores en este estado" en lugar de la tabla.
6. Finaliza con una sección de **Recomendaciones de Gestión** con 2 a 3 acciones clave escritas en viñetas claras.
7. NO incluyas el modelo de Kurt Lewin en este resumen; existe un reporte separado para eso.
8. NO inventes datos. Limítate estrictamente a la información provista.
"""

    return _ai["generate"](prompt, temperature=0.2, max_tokens=3000)


def generar_kurt_lewin_panel(gestion_nombre, periodo_nombre, seguimiento):
    """
    Genera un análisis de implementación del modelo de Kurt Lewin para los indicadores no concluidos.
    """

    indicadores_str = ""
    for f in seguimiento:
        avance = f["avance_tipo_1"]
        avance_str = f"{avance:.2f}%" if avance is not None else "Sin dato"
        indicadores_str += f"- {f['codigo']}: {f['nombre_indicador']} | Avance: {avance_str} | Estado: {f['estado']['nombre']}\n"

    prompt = f"""Eres un analista experto en gestión del cambio, gestión pública y monitoreo de indicadores.
Aplica el modelo de Kurt Lewin al desempeño institucional del periodo {periodo_nombre} de la gestión {gestion_nombre}.

INDICADORES DISPONIBLES:
{indicadores_str}

## IMPLEMENTACIÓN DEL MODELO DE KURT LEWIN

Aplica el modelo únicamente a los indicadores que todavía no han concluido:

- **Críticos:** avance menor al 75 % o sin dato.
- **En seguimiento:** avance desde 75 % hasta menos del 95 %.
- No analices ni muestres indicadores concluidos con avance igual o superior al 95 %.
- Utiliza siempre el código y el nombre completo y exacto de cada indicador.
- Ordena primero los indicadores críticos y después los indicadores en seguimiento.

Aplica estas reglas del modelo:

- **Descongelar:** establecer la línea base, realizar la medición inicial, diagnosticar la situación e identificar la necesidad de cambio.
- **Cambiar:** implementar acciones de mejora, realizar seguimiento y cerrar progresivamente las brechas.
- **Recongelar:** mantener el resultado alcanzado, estandarizar la mejora y aplicar controles o auditorías permanentes.

### 1. Descongelar

Explica brevemente que esta etapa permite reconocer la situación inicial, identificar las brechas y justificar la necesidad de intervenir los indicadores que todavía no alcanzan la meta.

Después, presenta obligatoriamente esta tabla:

| Código | Nombre completo del indicador | Línea base o avance actual | Estado | Brecha respecto al 95 % | Diagnóstico y necesidad de cambio |
|---|---|---:|---|---:|---|

Para completar la tabla:

- Incluye todos los indicadores críticos y en seguimiento.
- Utiliza el avance actual como línea base o medición inicial.
- Calcula la brecha en puntos porcentuales respecto al 95 %.
- Si el indicador no tiene avance, escribe “Sin dato” y no calcules una brecha inexistente.
- En **Diagnóstico y necesidad de cambio**, explica qué revela el resultado y qué aspecto del indicador necesita mejorar.
- El diagnóstico debe relacionarse directamente con lo que mide cada indicador.
- No escribas diagnósticos genéricos ni repitas el mismo texto.
- No inventes causas que no puedan deducirse del nombre, avance y estado del indicador.

Después de la tabla, agrega:

#### Principales necesidades de cambio identificadas

Presenta de 2 a 4 viñetas que resuman las brechas más importantes. Prioriza los indicadores críticos.

### 2. Cambiar

Explica brevemente que esta etapa comprende la implementación de acciones correctivas y de mejora para cerrar las brechas detectadas.

Después, presenta obligatoriamente esta tabla:

| Código | Nombre completo del indicador | Situación que debe corregirse | Acción de mejora propuesta | Forma de verificar el avance | Prioridad | Resultado esperado |
|---|---|---|---|---|---|---|

Para completar la tabla:

- Incluye los mismos indicadores críticos y en seguimiento analizados en Descongelar.
- En **Situación que debe corregirse**, resume claramente el problema evidenciado.
- En **Acción de mejora propuesta**, plantea una acción concreta y directamente relacionada con lo que mide el indicador.
- En **Forma de verificar el avance**, indica qué resultado, registro, prueba, medición o control relacionado con el indicador debe revisarse.
- Las acciones deben ser diferentes y específicas para cada indicador.
- Asigna prioridad **Alta** a los indicadores críticos o sin dato.
- Asigna prioridad **Media** a los indicadores en seguimiento.
- En **Resultado esperado**, indica que debe alcanzar como mínimo el 95 %.
- No inventes fechas, responsables, presupuestos o recursos no proporcionados.

Después de la tabla, agrega:

#### Orientación para ejecutar el cambio

Explica que las acciones deben comenzar por los indicadores críticos y que cada nuevo resultado debe compararse con la línea base.

### 3. Recongelar

Explica brevemente que esta etapa busca consolidar las mejoras aplicadas y evitar retrocesos.

Después, presenta obligatoriamente esta tabla:

| Código | Nombre completo del indicador | Mejora que debe mantenerse | Acción de estandarización | Control o auditoría requerida | Criterio de consolidación |
|---|---|---|---|---|---|

Para completar la tabla:

- Incluye los mismos indicadores analizados en Descongelar y Cambiar.
- En **Mejora que debe mantenerse**, explica qué resultado alcanzado no debe volver a disminuir.
- En **Acción de estandarización**, indica qué procedimiento, práctica, validación, registro o control debe documentarse e incorporarse al proceso.
- En **Control o auditoría requerida**, indica cómo se comprobará la permanencia de la mejora.
- En **Criterio de consolidación**, escribe que el indicador debe alcanzar y mantener un resultado igual o superior al 95 %.
- Las acciones deben ser específicas para cada indicador.
- No utilices el mismo texto genérico en todas las filas.

Después de la tabla, agrega:

#### Acciones para institucionalizar el cambio

Presenta de 2 a 4 viñetas sobre documentar mejoras, actualizar procedimientos, mantener mediciones y aplicar acciones correctivas ante desviaciones.

### 4. Monitoreo y mejora continua

Presenta obligatoriamente esta tabla:

| Código | Nombre completo del indicador | Estado inicial | Seguimiento requerido | Decisión ante desviaciones |
|---|---|---|---|---|

Incluye solamente los indicadores críticos y en seguimiento.

Finaliza señalando que el cambio se considerará consolidado cuando los indicadores intervenidos alcancen y mantengan un resultado igual o superior al 95 %, las mejoras estén documentadas y su cumplimiento continúe verificándose mediante mediciones, controles o auditorías.

REGLA OBLIGATORIA DE COMPLETITUD:

- Cada tabla debe contener una fila completa por cada indicador crítico y en seguimiento proporcionado.
- Está prohibido utilizar `...`, puntos suspensivos, “etc.”, “demás indicadores”, filas de ejemplo, filas resumidas o cualquier marcador que sustituya indicadores.
- No omitas ningún indicador crítico o en seguimiento.
- No acortes ni elimines columnas de las tablas solicitadas.
- No cambies los encabezados establecidos.
- Repite el código y el nombre completo del indicador en cada tabla donde corresponda.
- No inventes datos. Limítate estrictamente a la información provista.
"""

    return _ai["generate"](prompt, temperature=0.2, max_tokens=6000)


def consultar_asistente(mensaje, historial, context_data):
    """
    Responde consultas del usuario utilizando el contexto estructurado de la base de datos.
    """

    # Construir historial para la API
    historial_filtrado = []
    
    # Instrucción del sistema
    system_instruction = f"""Eres el Asistente de Gestión Oficial del sistema de monitoreo de procesos.
Tu objetivo es responder preguntas del usuario de forma útil, concisa y basada estrictamente en la información de la base de datos provista en este prompt.

CONTEXTO INSTITUCIONAL (Gestión {context_data['gestion']}):
- Objetivos Estratégicos: {json.dumps(context_data['objetivos'])}
- Catálogo de Procesos de la Institución: {json.dumps(context_data['procesos'])}
- Indicadores (con su Meta Anual y Avance actual): {json.dumps(context_data['indicadores'])}
- Líneas Base de los Indicadores: {json.dumps(context_data['lineas_base'])}
- Metas Mensuales y Valores Obtenidos por mes: {json.dumps(context_data['valores_mensuales'])}

REGLAS DE RESPUESTA:
1. Responde de forma cordial, breve y profesional.
2. Utiliza Markdown para dar formato a las listas, tablas o negritas cuando sea útil.
3. Limítate estrictamente a los datos provistos en el contexto de arriba. Si el usuario te pregunta sobre algo que no está en el contexto, di amablemente que no posees esa información.
4. **SEGURIDAD**: Bajo ninguna circunstancia respondas sobre usuarios, contraseñas, accesos, o la tabla de usuarios. No tienes acceso a esa información.
5. NO inventes datos ni asumas resultados que no estén explícitamente listados.
"""

    # Filtrar solo los últimos 6 mensajes del historial recibido para evitar sobrecarga
    # Mapeamos 'assistant' a 'model' y 'user' a 'user'
    for h in historial[:-1]:
        role_name = "user" if h.get("role") == "user" else "model"
        text_val = h.get("text") or ""
        # Evitar incluir el primer mensaje de bienvenida estático
        if "¡Hola! Soy tu asistente" in text_val:
            continue
        historial_filtrado.append({
            "role": role_name,
            "parts": [{"text": text_val}]
        })

    # Agregar la consulta actual junto con la instrucción del sistema
    prompt_completo = f"{system_instruction}\n\nConsulta del usuario: {mensaje}"
    historial_filtrado.append({
        "role": "user",
        "parts": [{"text": prompt_completo}]
    })

    return _ai["chat"](historial_filtrado, temperature=0.3, max_tokens=1500)


def consultar_asistente_wizard(mensaje, historial, context_data, system_instruction_add=""):
    """
    Responde consultas del usuario utilizando el contexto estructurado de la base de datos
    e incorporando instrucciones adicionales para guiar el asistente interactivo de vinculación.
    """

    # Construir historial para la API
    historial_filtrado = []
    
    # Instrucción del sistema
    system_instruction = f"""Eres el Asistente de Gestión Oficial del sistema de monitoreo de procesos.
Tu objetivo es responder preguntas del usuario de forma útil, concisa y basada estrictamente en la información de la base de datos provista en este prompt.

CONTEXTO INSTITUCIONAL (Gestión {context_data['gestion']}):
- Objetivos Estratégicos: {json.dumps(context_data['objetivos'])}
- Catálogo de Procesos de la Institución: {json.dumps(context_data['procesos'])}
- Indicadores (con su Meta Anual y Avance actual): {json.dumps(context_data['indicadores'])}
- Líneas Base de los Indicadores: {json.dumps(context_data['lineas_base'])}
- Metas Mensuales y Valores Obtenidos por mes: {json.dumps(context_data['valores_mensuales'])}
- Vinculaciones Actuales entre Indicadores y Procesos: {json.dumps(context_data.get('vinculaciones_actuales', []))}

REGLAS DE RESPUESTA:
1. Responde de forma cordial, breve y profesional.
2. Utiliza Markdown para dar formato a las listas, tablas o negritas cuando sea útil.
3. Limítate estrictamente a los datos provistos en el contexto de arriba. Si el usuario te pregunta sobre algo que no está en el contexto, di amablemente que no posees esa información.
4. **SEGURIDAD**: Bajo ninguna circunstancia respondas sobre usuarios, contraseñas, accesos, o la tabla de usuarios. No tienes acceso a esa información.
5. NO inventes datos ni asumas resultados que no estén explícitamente listados.
{system_instruction_add}
"""

    # Filtrar solo los últimos 6 mensajes del historial recibido para evitar sobrecarga
    # Mapeamos 'assistant' a 'model' y 'user' a 'user'
    for h in historial[:-1]:
        role_name = "user" if h.get("role") == "user" else "model"
        text_val = h.get("text") or ""
        # Evitar incluir el primer mensaje de bienvenida estático
        if "¡Hola! Soy tu asistente" in text_val:
            continue
        historial_filtrado.append({
            "role": role_name,
            "parts": [{"text": text_val}]
        })

    # Agregar la consulta actual junto con la instrucción del sistema
    prompt_completo = f"{system_instruction}\n\nConsulta del usuario: {mensaje}"
    historial_filtrado.append({
        "role": "user",
        "parts": [{"text": prompt_completo}]
    })

    return _ai["chat"](historial_filtrado, temperature=0.3, max_tokens=1500)
