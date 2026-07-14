import os
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

def generar_resumen_panel(gestion_nombre, periodo_nombre, total_indicadores, evaluados, avance_acciones, avance_objetivos, conteo_estados, seguimiento):
    """
    Genera un análisis narrativo del panel de control utilizando la API de Google Gemini (Studio).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("No se ha configurado la variable de entorno GEMINI_API_KEY")
        return "Error: No se ha configurado la API Key de Gemini en el archivo .env."

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
7. NO inventes datos. Limítate estrictamente a la información provista.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 3000
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        # Timeout de 30 segundos
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                parts = res_data["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "No se recibió texto de respuesta de la IA.")
            return "Error: Respuesta inválida o vacía de la API de Gemini."
    except Exception as e:
        logger.exception("Error al llamar a la API de Gemini")
        return f"Error de comunicación con la IA: {str(e)}"
