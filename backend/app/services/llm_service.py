import json
import time
import google.generativeai as genai
from google.api_core import exceptions
from ..config import get_settings

_model = None


def _get_model():
    global _model
    if _model is None:
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel("gemini-flash-latest")
    return _model


def _call_with_retry(func, *args, **kwargs):
    max_retries = 3
    base_delay = 2
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable) as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            print(f"LLM rate limit or service error. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            raise e


def generate(prompt: str, system_prompt: str = "") -> str:
    """Send a prompt to Gemini and return the text response."""
    model = _get_model()
    contents = []
    if system_prompt:
        contents.append({"role": "user", "parts": [system_prompt + "\n\n" + prompt]})
    else:
        contents.append({"role": "user", "parts": [prompt]})
    
    response = _call_with_retry(
        model.generate_content,
        contents,
        generation_config=genai.GenerationConfig(temperature=0),
    )
    return response.text


def generate_json(prompt: str, system_prompt: str = "") -> list | dict:
    """Send a prompt to Gemini expecting a JSON response."""
    model = _get_model()
    full_prompt = (system_prompt + "\n\n" + prompt) if system_prompt else prompt
    
    response = _call_with_retry(
        model.generate_content,
        full_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    text = response.text.strip()
    return json.loads(text)
