"""
engine/llm_client.py

Calls the Ollama container running deepseek-coder:6.7b-instruct (Q4_K_M GGUF).

Environment variables (set in docker-compose):
    OLLAMA_HOST   — defaults to "http://deepseek_api:11434"
    OLLAMA_MODEL  — defaults to "deepseek-coder:6.7b-instruct"
    LLM_TIMEOUT   — request timeout in seconds (default 120)

Ollama /api/generate docs:
  https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion
"""
import os
import logging

import requests

logger = logging.getLogger(__name__)

_OLLAMA_HOST  = os.environ.get("OLLAMA_HOST",  "http://deepseek_api:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-coder:6.7b-instruct")
_TIMEOUT      = int(os.environ.get("LLM_TIMEOUT", 120))

# Generation parameters tuned for deterministic SQL output
_GEN_OPTIONS = {
    "temperature":   0.0,   # fully deterministic
    "top_p":         0.9,
    "repeat_penalty":1.1,
    "num_predict":   256,   # SQL rarely exceeds 256 tokens
    "stop":          ["\n\n", "###", "```"],  # stop at explanation attempts
}


def call_llm(prompt: str) -> str:
    """
    Sends prompt to Ollama and returns the raw LLM text.

    Raises:
        RuntimeError  if Ollama is unreachable or returns a non-200 status.
        ValueError    if the response JSON has no 'response' key.
    """
    url     = f"{_OLLAMA_HOST}/api/generate"
    payload = {
        "model":   _OLLAMA_MODEL,
        "prompt":  prompt,
        "stream":  False,
        "options": _GEN_OPTIONS,
    }

    logger.info(f"llm_client: POST {url} model={_OLLAMA_MODEL}")

    try:
        resp = requests.post(url, json=payload, timeout=_TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot reach Ollama at {_OLLAMA_HOST}. "
            "Is the llm_model container running?"
        ) from e
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama did not respond within {_TIMEOUT}s. "
            "The model may still be loading — try again shortly."
        )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Ollama returned HTTP {resp.status_code}: {resp.text[:300]}"
        )

    data = resp.json()
    if "response" not in data:
        raise ValueError(f"Unexpected Ollama response shape: {data}")

    raw = data["response"].strip()
    logger.info(f"llm_client: received {len(raw)} chars from model")
    return raw