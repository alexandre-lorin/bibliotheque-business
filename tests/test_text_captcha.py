import asyncio
import io
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

import anna_browser
import text_captcha


def fixture_png():
    image = Image.new('RGB', (180, 80), 'white')
    ImageDraw.Draw(image).text((12, 12), 'AB12', font=ImageFont.load_default(size=44), fill='black')
    output = io.BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


class Handler(BaseHTTPRequestHandler):
    attempts = 0
    ip_clicks = 0

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/delayed':
            content = (b'<title>DDoS-Guard</title><h1>Checking your browser</h1>'
                       b'<button onclick="location.href=\'/ip\'">Show IP address</button>'
                       b'<iframe id="puzzle" src="/puzzle-frame" style="visibility:hidden"></iframe>'
                       b'<script>setTimeout(()=>document.querySelector("#puzzle").style.visibility="visible",900)</script>')
            mime = 'text/html'
        elif path == '/ip':
            Handler.ip_clicks += 1
            content, mime = b'<title>Not a verification action</title>', 'text/html'
        elif path == '/image.png':
            content, mime = fixture_png(), 'image/png'
        elif path == '/done' and parse_qs(urlsplit(self.path).query).get('captcha') == ['AB12']:
            Handler.attempts += 1
            content = b'<title>Catalogue</title><main><a href="/md5/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa">Livre de test</a></main>'
            mime = 'text/html'
        else:
            if path == '/done':
                Handler.attempts += 1
            content = (b'<title>DDoS-Guard</title><h1>Verify you are human</h1>'
                       b'<form action="/done" target="_top"><img width="180" height="80" src="/image.png">'
                       b'<input name="captcha" maxlength="4"><button type="submit">Verify</button></form>')
            mime = 'text/html'
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass


@unittest.skipUnless((text_captcha.ROOT / '.venv-ocr/bin/python').exists(), 'Environnement OCR optionnel absent')
class TextCaptchaTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_local_ocr_reads_generated_image(self):
        result = await text_captcha.read_image(fixture_png(), engine='ddddocr')
        self.assertEqual(result['status'], 'recognized')
        self.assertEqual(result['text'], 'AB12')

    async def test_actual_browser_and_actual_ocr_complete_one_submission(self):
        result = await self.flow()
        self.assertEqual(result['status'], 'catalog_ready', result)
        self.assertEqual(Handler.attempts, 1)
        self.assertEqual(result['results'][0]['title'], 'Livre de test')

    async def test_wait_for_form_never_clicks_show_ip(self):
        result = await self.flow('/delayed')
        self.assertEqual(result['status'], 'catalog_ready', result)
        self.assertEqual(Handler.ip_clicks, 0)
        self.assertEqual(Handler.attempts, 1)

    async def test_ambiguous_recognition_is_not_submitted(self):
        with patch('text_captcha.read_image', new=AsyncMock(return_value={'status': 'recognition_ambiguous'})):
            result = await self.flow()
        self.assertEqual(result['status'], 'captcha_required')
        self.assertEqual(Handler.attempts, 0)

    async def test_rejected_answer_is_not_retried(self):
        with patch('text_captcha.read_image', new=AsyncMock(return_value={'status': 'recognized', 'text': 'ZZZZ'})):
            result = await self.flow()
        self.assertEqual(result['status'], 'captcha_required')
        self.assertEqual(result['ocr_status'], 'ocr_not_accepted')
        self.assertEqual(Handler.attempts, 1)

    async def flow(self, path='/puzzle'):
        Handler.attempts = 0
        Handler.ip_clicks = 0
        http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    context = await browser.new_context()
                    with tempfile.TemporaryDirectory() as root:
                        with patch.dict(os.environ, {'TOUBI_CAPTCHA_OCR_BACKEND': 'ddddocr'}):
                            return await asyncio.wait_for(anna_browser.drive(
                                context, f'http://127.0.0.1:{http.server_port}{path}', root=Path(root),
                                _allow_local_fixture=True, text_captcha_ocr=True), 15)
                finally:
                    await browser.close()
        finally:
            http.shutdown()
            http.server_close()
            thread.join()
