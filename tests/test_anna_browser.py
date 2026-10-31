import asyncio
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

import anna_browser

MD5 = 'a' * 32
PAYLOAD = ('Document original de recette pour vérifier le téléchargement et son import.\n' * 10).encode()


class Handler(BaseHTTPRequestHandler):
    requests = []
    request_urls = []
    require_verification = False

    def do_GET(self):
        path = urlsplit(self.path).path
        self.requests.append(path)
        self.request_urls.append(self.path)
        status = 200
        attachment = False
        extra_headers = []
        if path == '/search':
            if self.require_verification and 'verified=yes' not in self.headers.get('Cookie', ''):
                body = b'<h1>Verify you are human</h1>'
            else:
                body = (f'<nav><a href="/md5/{"b" * 32}">Livre hors recherche</a></nav>'
                        f'<main><h1>Catalogue</h1><a href="/md5/{MD5}">Livre de recette</a></main>').encode()
        elif path == '/passed':
            status = 302
            body = b''
            extra_headers = [('Set-Cookie', 'verified=yes; Path=/'), ('Location', '/search')]
        elif path == '/parent-catalog':
            body = f'<title>Catalogue</title><main><a href="/md5/{MD5}">Livre de recette</a></main><iframe src="/child-denied"></iframe>'.encode()
        elif path == '/child-denied':
            status = 403
            body = b'<h1>Access denied in child frame</h1>'
        elif path == '/md5/' + MD5:
            body = b'<h1>Livre de recette</h1><a href="/slow_download/unit">Slow download</a><a href="/premium">Fast download</a>'
        elif path == '/slow_download/unit':
            body = b'''<h1>Free download</h1><p>Wait for the countdown</p>
                <button disabled id="file" onclick="location.href='/attachment?token=test-only'">Download file</button>
                <script>setTimeout(()=>document.querySelector('#file').disabled=false,1100)</script>'''
        elif path == '/attachment':
            body = PAYLOAD
            attachment = True
        elif path == '/captcha':
            body = b'<h1>Verify you are human</h1><button onclick="location.href=\'/verify\'">Verify</button>'
        elif path == '/login':
            body = b'<h1>Sign in</h1><input type="password"><button>Download</button>'
        elif path == '/quota':
            status = 429
            body = b'<h1>Too many requests</h1>'
        elif path == '/parked':
            body = b'<h1>annas-archive.example</h1>This domain may be for sale.'
        elif path == '/empty':
            body = b'<h1>Book notice</h1><a href="/premium">Fast download</a>'
        elif path == '/membership':
            body = b'<h1>Membership required</h1><button onclick="location.href=\'/premium\'">Download</button>'
        else:
            status = 404
            body = b'<h1>Not found</h1>'
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain' if attachment else 'text/html')
        if attachment:
            self.send_header('Content-Disposition', 'attachment; filename="book.txt"')
        self.send_header('Content-Length', str(len(body)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class BrowserIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Vrai Chromium et serveur HTTP de recette ; aucun site distant simulé comme validé."""

    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.http.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    async def asyncSetUp(self):
        Handler.requests = []
        Handler.request_urls = []
        Handler.require_verification = False
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(accept_downloads=True)
        self.context.set_default_timeout(2000)

    async def asyncTearDown(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()
        self.temp.cleanup()

    async def flow(self, path, metadata=None):
        return await asyncio.wait_for(anna_browser.drive(self.context, self.base + path, metadata,
                                                       root=self.root, _allow_local_fixture=True), timeout=12)

    async def test_real_search_extracts_public_notices(self):
        result = await self.flow('/search')
        self.assertEqual(result['status'], 'catalog_ready')
        self.assertEqual(result['results'][0]['md5'], MD5)
        self.assertEqual(result['results'][0]['title'], 'Livre de recette')
        self.assertEqual(len(result['results']), 1)

    async def test_child_frame_denial_does_not_poison_main_page_status(self):
        result = await self.flow('/parent-catalog')
        self.assertEqual(result['status'], 'catalog_ready', result)
        self.assertEqual(result['results'][0]['md5'], MD5)

    async def test_real_click_countdown_download_and_import_without_key(self):
        start = time.monotonic()
        result = await self.flow('/md5/' + MD5, {'title': 'Livre de recette', 'author': 'Toubi',
                                               'rights': 'authorized', 'evidence': 'Texte original de recette', 'suffix': '.txt'})
        self.assertEqual(result['status'], 'downloaded_imported')
        self.assertGreater(time.monotonic() - start, 1.0)
        self.assertEqual(result['steps'], 2)
        self.assertNotIn('/premium', Handler.requests)
        doc = (self.root / result['import']['path']).read_text()
        self.assertNotIn('token=', doc)
        self.assertNotIn('test-only', doc)
        self.assertIn(PAYLOAD.decode().strip(), doc)
        archived = list((self.root / 'archives' / 'imports').glob('*'))
        self.assertEqual(archived[0].read_bytes(), PAYLOAD)

    async def test_captcha_stops_before_clicking(self):
        result = await self.flow('/captcha', {'title': 'Recette'})
        self.assertEqual(result['status'], 'captcha_required')
        self.assertEqual(result['steps'], 0)
        self.assertNotIn('/verify', Handler.requests)

    async def test_authentication_is_not_attempted(self):
        result = await self.flow('/login', {'title': 'Recette'})
        self.assertEqual(result['status'], 'authentication_required')
        self.assertEqual(result['steps'], 0)

    async def test_parked_domain_is_recognized(self):
        result = await self.flow('/parked')
        self.assertEqual(result['status'], 'domain_parked')

    async def test_quota_is_not_retried(self):
        result = await self.flow('/quota')
        self.assertEqual(result['status'], 'rate_limited')
        self.assertEqual(Handler.requests.count('/quota'), 1)

    async def test_paid_only_page_does_not_get_clicked(self):
        result = await self.flow('/empty', {'title': 'Recette'})
        self.assertEqual(result['status'], 'no_free_link')
        self.assertNotIn('/premium', Handler.requests)

    async def test_membership_gate_stops_before_download(self):
        result = await self.flow('/membership', {'title': 'Recette'})
        self.assertEqual(result['status'], 'payment_required')
        self.assertNotIn('/premium', Handler.requests)

    async def test_download_format_mismatch_is_not_imported(self):
        result = await self.flow('/md5/' + MD5, {'title': 'Recette', 'rights': 'authorized',
                                               'evidence': 'Test', 'suffix': '.pdf'})
        self.assertEqual(result['status'], 'format_mismatch')
        self.assertFalse((self.root / 'contenus').exists())

    async def test_manual_challenge_waits_and_resumes_same_browser_context(self):
        notices = []
        task = asyncio.create_task(anna_browser.drive(
            self.context, self.base + '/captcha', root=self.root,
            _allow_local_fixture=True, manual_captcha=True, on_manual_challenge=notices.append))
        try:
            for _ in range(40):
                if notices:
                    break
                await asyncio.sleep(0.05)
            self.assertEqual(notices[0]['status'], 'manual_captcha_wait')
            self.assertFalse(task.done())
            self.assertNotIn('/verify', Handler.requests)
            # La recette reproduit une navigation humaine terminée ; aucun solveur n'est appelé.
            page = self.context.pages[-1]
            await page.goto(self.base + '/search')
            result = await asyncio.wait_for(task, 5)
            self.assertEqual(result['status'], 'catalog_ready')
            self.assertEqual(result['results'][0]['md5'], MD5)
            self.assertEqual(len(self.context.pages), 1)
        finally:
            if not task.done():
                task.cancel()

    async def test_query_is_restored_after_manual_redirect_and_session_reuses_memory(self):
        Handler.require_verification = True
        notices = []
        target = self.base + '/search?q=original-query'
        task = asyncio.create_task(anna_browser.drive(
            self.context, target, root=self.root, _allow_local_fixture=True,
            manual_captcha=True, on_manual_challenge=notices.append))
        try:
            for _ in range(40):
                if notices:
                    break
                await asyncio.sleep(0.05)
            self.assertTrue(notices)
            # Navigation de recette représentant l'utilisateur qui a terminé la vérification.
            await self.context.pages[-1].goto(self.base + '/passed')
            result = await asyncio.wait_for(task, 5)
            self.assertEqual(result['status'], 'catalog_ready')
            self.assertEqual(Handler.request_urls.count('/search?q=original-query'), 2)
            self.assertEqual(result['results'][0]['md5'], MD5)
            again = await anna_browser.drive(self.context, self.base + '/search?q=next-query',
                                             root=self.root, _allow_local_fixture=True,
                                             manual_captcha=True, on_manual_challenge=notices.append)
            self.assertEqual(again['status'], 'catalog_ready')
            self.assertEqual(len(notices), 1)
        finally:
            if not task.done():
                task.cancel()


class URLTests(unittest.TestCase):
    def test_signed_urls_and_local_targets(self):
        self.assertEqual(anna_browser.public_url('https://example.org/file?token=unit#fragment'), 'https://example.org/file')
        self.assertFalse(anna_browser.public_target('http://example.org/file'))
        self.assertFalse(anna_browser.public_target('https://127.0.0.1/file'))
        self.assertFalse(anna_browser.public_target('https://user:password@example.org'))
        self.assertEqual(anna_browser.link_priority('Fast download', '/fast_download/123'), 0)
        self.assertEqual(anna_browser.link_priority('Verify', '/captcha'), 0)
        with self.assertRaises(ValueError):
            anna_browser.normalize_target('https://another.example/md5/' + MD5, 'https://annas-archive.li')


if __name__ == '__main__':
    unittest.main()
