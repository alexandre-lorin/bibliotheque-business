"""Lecture d'image par le modèle vision déjà installé dans Ollama, en local seulement."""
import asyncio
import base64
import json
import re
from urllib.request import Request, urlopen

MODEL = 'qwen3.5:2b'
ENDPOINT = 'http://127.0.0.1:11434'


def call(path, payload, timeout):
    request = Request(ENDPOINT + path, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def recognize_sync(raw):
    if not raw or len(raw) > 2_000_000:
        return {'status': 'image_too_large'}
    try:
        capabilities = call('/api/show', {'model': MODEL}, 2).get('capabilities', [])
        if 'vision' not in capabilities:
            return {'status': 'vision_unavailable'}
        result = call('/api/chat', {
            'model': MODEL,
            'messages': [{'role': 'user', 'content': 'Transcribe the alphanumeric characters in the image from left to right. Preserve case. Return JSON with a single text field and no explanation.',
                          'images': [base64.b64encode(raw).decode()]}],
            'format': {'type': 'object', 'properties': {'text': {'type': 'string'}}, 'required': ['text'], 'additionalProperties': False},
            'stream': False, 'think': False, 'keep_alive': '30s',
            'options': {'temperature': 0, 'num_predict': 64, 'num_ctx': 2048},
        }, 25)
        text = json.loads(result['message']['content']).get('text', '').strip()
        if not re.fullmatch(r'[A-Za-z0-9]{3,10}', text):
            return {'status': 'vision_unreadable'}
        return {'status': 'predicted', 'text': text, 'engine': MODEL, 'agreement': None}
    except Exception:
        return {'status': 'vision_unavailable'}


async def recognize(raw):
    return await asyncio.to_thread(recognize_sync, raw)
