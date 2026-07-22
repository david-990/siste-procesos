import os
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)


def _http_post(url, payload, headers=None):
    """Realiza una petición POST HTTP y devuelve el texto crudo de respuesta."""
    req_headers = headers or {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=req_headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def call_gemini(prompt, temperature=0.2, max_tokens=3000):
    """Envía un prompt a Gemini y devuelve el texto generado."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY no configurada")
        return "Error: No se ha configurado la API Key de Gemini en el archivo .env."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    try:
        raw = _http_post(url, payload)
        data = json.loads(raw)
        if "candidates" in data and len(data["candidates"]) > 0:
            parts = data["candidates"][0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "No se recibió texto de respuesta de la IA.")
        return "Error: Respuesta inválida o vacía de la API de Gemini."
    except Exception as e:
        logger.exception("Error al llamar a la API de Gemini")
        return f"Error de comunicación con la IA: {str(e)}"


def call_gemini_chat(messages, temperature=0.3, max_tokens=1500):
    """Envía un historial de mensajes a Gemini (formato Gemini) y devuelve el texto generado."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY no configurada")
        return "Error: No se ha configurado la API Key de Gemini en el archivo .env."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
    payload = {
        "contents": messages,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    try:
        raw = _http_post(url, payload)
        data = json.loads(raw)
        if "candidates" in data and len(data["candidates"]) > 0:
            parts = data["candidates"][0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "No se pudo obtener respuesta del asistente.")
        return "Respuesta vacía del asistente."
    except Exception as e:
        logger.exception("Error en el chatbot de Gemini")
        return f"Error de comunicación con el asistente de IA: {str(e)}"


def call_openai(prompt, temperature=0.2, max_tokens=3000):
    """Envía un prompt a OpenAI y devuelve el texto generado."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY no configurada")
        return "Error: No se ha configurado la API Key de OpenAI en el archivo .env."

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        raw = _http_post(url, payload, headers)
        data = json.loads(raw)
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0].get("message", {}).get("content", "")
        return "Error: Respuesta inválida o vacía de la API de OpenAI."
    except Exception as e:
        logger.exception("Error al llamar a la API de OpenAI")
        return f"Error de comunicación con la IA: {str(e)}"


def call_openai_chat(messages, temperature=0.3, max_tokens=1500):
    """Convierte mensajes de formato Gemini a OpenAI y envía el historial."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY no configurada")
        return "Error: No se ha configurado la API Key de OpenAI en el archivo .env."

    # Convertir de formato Gemini → OpenAI
    openai_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        openai_role = "assistant" if role == "model" else role
        parts = msg.get("parts", [])
        text = parts[0].get("text", "") if parts else ""
        openai_messages.append({"role": openai_role, "content": text})

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": openai_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        raw = _http_post(url, payload, headers)
        data = json.loads(raw)
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0].get("message", {}).get("content", "")
        return "Respuesta vacía del asistente."
    except Exception as e:
        logger.exception("Error en el chatbot de OpenAI")
        return f"Error de comunicación con el asistente de IA: {str(e)}"


def get_provider():
    """Devuelve un dict con funciones 'generate' y 'chat' según AI_PROVIDER."""
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    if provider == "openai":
        return {"generate": call_openai, "chat": call_openai_chat}
    return {"generate": call_gemini, "chat": call_gemini_chat}
