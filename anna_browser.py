#!/usr/bin/env python3
"""Parcours navigateur gratuit : recherche, clics exposés, attente et import. Sans clé."""
import asyncio
import hashlib
import ipaddress
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

import books

ROOT = books.ROOT
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / '.cache' / 'playwright'))


def public_url(url):
    """URL de rapport : aucun paramètre signé, fragment ou identifiant."""
    p = urlsplit(url)
    host = p.hostname or ''
    if ':' in host:
        host = '[' + host + ']'
    if p.port:
        host += ':' + str(p.port)
    return urlunsplit((p.scheme, host, p.path, '', ''))


def public_target(url):
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password:
        return False
    if p.hostname in ('localhost',) or p.hostname.endswith(('.local', '.localhost')):
        return False
    try:
        return ipaddress.ip_address(p.hostname).is_global
    except ValueError:
        return True


def normalize_target(target, base):
    books.anna_url('', base)
    p = urlsplit(base)
    if p.path not in ('', '/') or p.query or p.fragment or p.username or p.password:
        raise ValueError('Fournir seulement le domaine HTTPS dans --base')
    if re.fullmatch(r'[a-fA-F0-9]{32}', target):
        return base.rstrip('/') + '/md5/' + target.lower()
    supplied = urlsplit(target)
    if supplied.scheme != 'https' or supplied.hostname != p.hostname or supplied.query or supplied.fragment:
        raise ValueError('Fournir un MD5 ou une fiche publique du même domaine que --base')
    if not re.fullmatch(r'/md5/[a-fA-F0-9]{32}', supplied.path):
        raise ValueError('Fiche /md5/IDENTIFIANT attendue')
    return public_url(target)


def blocked_text(title, text, status=None):
    lower = (title + '\n' + text).casefold()
    if status in (401,):
        return 'authentication_required'
    if status == 429:
        return 'rate_limited'
    if status == 402:
        return 'payment_required'
    if any(x in lower for x in ('this domain may be for sale', 'this domain is for sale', 'buy this domain', 'domain is parked')):
        return 'domain_parked'
    if any(x in lower for x in ('verify you are human', 'verify that you are human', 'checking your browser',
                                'vérifiez que vous êtes humain', 'just a moment...', 'complete the captcha')):
        return 'captcha_required'
    if 'ddosguard' in title.casefold().replace('-', '') and status != 451:
        return 'captcha_required'
    if status in (403, 451):
        return 'access_denied'
    if status is not None and status >= 500:
        return 'site_unavailable'
    if any(x in lower for x in ('download quota exceeded', 'daily download limit reached', 'download limit exceeded')):
        return 'quota_reached'
    return None


def link_priority(text, href):
    label = ' '.join(text.casefold().split())
    path = urlsplit(href or '').path.casefold()
    # Ne jamais cliquer un contrôle d'authentification, de paiement ou de vérification.
    if any(x in label or x in path for x in ('captcha', 'verify', 'vérifier', 'login', 'log in', 'sign in',
                                            'donate', 'subscribe', 'premium', 'fast download', 'fast_download', 'payment')):
        return 0
    if 'slow_download' in path or re.search(r'\bslow downloads?\b', label) or 'téléchargement lent' in label:
        return 3
    if re.fullmatch(r'(download( file| now)?|télécharger( le fichier)?|get file)(\s*[→↓])?', label):
        return 2
    if label.startswith(('download from ', 'slow partner server', 'télécharger depuis ')):
        return 1
    return 0


async def page_block(page, status=None):
    try:
        text = await page.locator('body').inner_text(timeout=2000)
        blocked = blocked_text(await page.title(), text[:50000], status)
        if blocked:
            return blocked
        if await page.locator('input[type=password]:visible').count():
            return 'authentication_required'
        headings = page.get_by_role('heading', name=re.compile(r'^(membership required|members only|abonnement requis|paiement requis)$', re.I))
        for heading in await headings.all():
            if await heading.is_visible():
                return 'payment_required'
        for frame in await page.locator('iframe[src*=captcha],iframe[src*=challenges],iframe[src*=turnstile]').all():
            if await frame.is_visible():
                return 'captcha_required'
    except Exception:
        return 'page_unreadable'
    return None


async def catalog(page, limit=10):
    records = []
    seen = set()
    scope = page.locator('main').first if await page.locator('main').count() else page
    for link in await scope.locator('a[href*="/md5/"]').all():
        href = await link.get_attribute('href') or ''
        target = urljoin(page.url, href)
        match = re.fullmatch(r'/md5/([a-fA-F0-9]{32})', urlsplit(target).path)
        if not match or urlsplit(target).hostname != urlsplit(page.url).hostname:
            continue
        identifier = match.group(1).lower()
        title = ' '.join((await link.inner_text()).split())[:300]
        if identifier in seen or not title:
            continue
        seen.add(identifier)
        records.append({'md5': identifier, 'title': title, 'url': public_url(target),
                        'notice': 'Notice affichée par le site ; droits et contenu du livre non vérifiés.'})
        if len(records) >= limit:
            break
    return records


async def free_candidate(page, clicked, _allow_local_fixture=False):
    candidates = []
    for element in await page.locator('a,button,input[type=submit]').all():
        if not await element.is_visible():
            continue
        label = (await element.inner_text()).strip() or (await element.get_attribute('value') or '')
        href = await element.get_attribute('href') or ''
        score = link_priority(label, href)
        if not score:
            continue
        key = (page.url, label, href)
        if key in clicked:
            continue
        # Un bouton désactivé est une attente, jamais un attribut à retirer.
        if not await element.is_enabled() or await element.get_attribute('aria-disabled') == 'true':
            continue
        if href:
            target = urljoin(page.url, href)
            local_test = _allow_local_fixture and urlsplit(target).hostname in ('127.0.0.1', 'localhost')
            if not public_target(target) and not local_test:
                continue
        candidates.append((score, element, key))
    return max(candidates, key=lambda c: c[0]) if candidates else None


async def save_import(download, metadata, source_url, root):
    suffix = Path(download.suggested_filename).suffix.lower()
    supported = ('.pdf', '.epub', '.txt', '.md', '.html')
    requested = metadata.get('suffix')
    if suffix not in supported or (requested and requested != suffix):
        await download.cancel()
        return {'status': 'format_mismatch'}
    with tempfile.TemporaryDirectory(prefix='toubi-anna-browser-') as folder:
        path = Path(folder) / ('document' + suffix)
        await download.save_as(str(path))
        if await download.failure():
            return {'status': 'download_failed'}
        if path.stat().st_size > books.MAX_BYTES:
            return {'status': 'file_too_large'}
        # Les liens signés et cookies ne quittent jamais le contexte temporaire.
        # Après réception, terminer l'import local sans thread détaché : un délai navigateur
        # ne doit pas annoncer un échec alors qu'un import continue en arrière-plan.
        result = books.import_file(path, metadata['title'], metadata.get('author', 'Non renseigné'),
                                   metadata['rights'], metadata['evidence'], metadata.get('language', 'fr'),
                                   source_url, 'anna-browser', root)
        return {'status': 'downloaded_imported', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'import': result}


async def _drive(context, url, metadata=None, limit=10, root=ROOT, _allow_local_fixture=False,
                 manual_captcha=False, on_manual_challenge=None, registrations=None, text_captcha_ocr=False):
    """Moteur de parcours. Le drapeau privé sert seulement à la recette HTTP locale."""
    from playwright.async_api import Error
    downloads = []
    pages = []
    last_status = {}
    async def restrict(route):
        scheme = urlsplit(route.request.url).scheme
        if _allow_local_fixture or scheme in ('data', 'blob', 'about') or public_target(route.request.url):
            await route.continue_()
        else:
            await route.abort()
    await context.route('**/*', restrict)
    def register(page):
        pages.append(page)
        page.on('download', lambda download: downloads.append(download))
        def response_received(response):
            if response.request.is_navigation_request() and response.request.frame == page.main_frame:
                last_status[page] = response.status
        page.on('response', response_received)
        page.on('dialog', lambda dialog: dialog.dismiss())
    context.on('page', register)
    if registrations is not None:
        registrations.append(('page', register))
    page = await context.new_page()
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=25000)
    except Error:
        if not downloads:
            return {'status': 'site_unavailable', 'url': public_url(url), 'steps': 0}
    clicked = set()
    steps = 0
    idle_checks = 0
    challenge_reported = False
    restored_query = False
    empty_reads = 0
    ocr_state = {}
    while True:
        if downloads:
            if metadata is None:
                await downloads[0].cancel()
                return {'status': 'unexpected_download', 'steps': steps}
            return {**await save_import(downloads[0], metadata, public_url(url), root), 'steps': steps}
        open_pages = [p for p in pages if not p.is_closed()]
        if not open_pages:
            return {'status': 'page_closed', 'steps': steps}
        page = open_pages[-1]
        if page.url == 'about:blank':
            await asyncio.sleep(0.3)
            continue
        blocked = await page_block(page, last_status.get(page))
        if blocked == 'captcha_required' and text_captcha_ocr:
            import text_captcha
            try:
                ocr_result = await text_captcha.advance(page, ocr_state)
            except Exception as exc:
                ocr_result = 'ocr_unavailable'
                ocr_state['attempted'] = True
                ocr_state['diagnostic'] = type(exc).__name__
            if ocr_result in ('ocr_challenge_loading', 'ocr_submitted_once', 'ocr_waiting_result'):
                if ocr_result == 'ocr_submitted_once':
                    print('OCR : une proposition envoyée ; vérification du résultat.', file=sys.stderr, flush=True)
                await asyncio.sleep(0.5)
                continue
            if not manual_captcha:
                return {'status': 'captcha_required', 'ocr_status': ocr_result,
                        'ocr_diagnostic': ocr_state.get('diagnostic'), 'steps': steps}
        if blocked == 'captcha_required' and manual_captcha:
            if not challenge_reported:
                message = {'status': 'manual_captcha_wait', 'url': public_url(page.url)}
                if on_manual_challenge:
                    on_manual_challenge(message)
                else:
                    print('CAPTCHA : validez-le dans la fenêtre dédiée ; le bot attend sans cliquer.', file=sys.stderr, flush=True)
                challenge_reported = True
            await asyncio.sleep(1)
            continue
        challenge_reported = False
        if blocked:
            return {'status': blocked, 'url': public_url(page.url), 'page_title': await page.title(), 'steps': steps}
        if metadata is None:
            wanted_query = parse_qs(urlsplit(url).query).get('q')
            current_query = parse_qs(urlsplit(page.url).query).get('q')
            if (wanted_query and wanted_query != current_query and not restored_query
                    and urlsplit(page.url).hostname == urlsplit(url).hostname):
                # Certaines validations humaines renvoient vers /search sans conserver q.
                # Restaurer une fois la recherche dans le même contexte déjà validé.
                restored_query = True
                await page.goto(url, wait_until='domcontentloaded', timeout=25000)
                continue
            results = await catalog(page, limit)
            if not results and empty_reads < 6:
                empty_reads += 1
                await asyncio.sleep(0.5)
                continue
            return {'status': 'catalog_ready', 'url': public_url(page.url), 'results': results}
        if steps >= 8:
            return {'status': 'step_limit', 'steps': steps}
        candidate = await free_candidate(page, clicked, _allow_local_fixture)
        if candidate:
            _, element, key = candidate
            clicked.add(key)
            steps += 1
            idle_checks = 0
            try:
                await element.click(timeout=10000, no_wait_after=True)
            except Error:
                if not downloads:
                    return {'status': 'navigation_failed', 'steps': steps}
        else:
            idle_checks += 1
            if idle_checks >= 3:
                text = (await page.locator('body').inner_text())[:30000].casefold()
                disabled = await page.locator('button:disabled,input[type=submit]:disabled,[aria-disabled=true]').count()
                waiting = disabled or re.search(r'\b(wait|attend|seconds?|secondes?|countdown)\b', text)
                if not waiting:
                    return {'status': 'no_free_link', 'url': public_url(page.url), 'steps': steps}
        await asyncio.sleep(0.5)


async def drive(context, url, metadata=None, limit=10, root=ROOT, _allow_local_fixture=False,
                manual_captcha=False, on_manual_challenge=None, text_captcha_ocr=False):
    registrations = []
    try:
        return await _drive(context, url, metadata, limit, root, _allow_local_fixture,
                            manual_captcha, on_manual_challenge, registrations, text_captcha_ocr)
    finally:
        for event, callback in registrations:
            context.remove_listener(event, callback)


async def run(url, metadata=None, limit=10, wait_seconds=180, headed=False, manual_captcha=False, text_captcha_ocr=False):
    from playwright.async_api import Error, async_playwright
    if not 1 <= wait_seconds <= 600:
        raise ValueError('Attente entre 1 et 600 secondes')
    if not public_target(url):
        raise ValueError('URL HTTPS publique requise')
    if metadata is not None and (metadata.get('rights') not in books.RIGHTS or not metadata.get('evidence', '').strip()):
        raise ValueError('Droits et provenance requis avant le parcours de téléchargement')
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not (headed or manual_captcha))
        context = await browser.new_context(accept_downloads=True)
        context.set_default_timeout(10000)
        try:
            async with asyncio.timeout(wait_seconds):
                return await drive(context, url, metadata, limit, manual_captcha=manual_captcha, text_captcha_ocr=text_captcha_ocr)
        except TimeoutError:
            return {'status': 'waiting_timeout', 'url': public_url(url)}
        except Error:
            return {'status': 'browser_error', 'url': public_url(url)}
        finally:
            await context.close()
            await browser.close()


async def resolve_base(base):
    if base != 'auto':
        normalize_target('0' * 32, base)
        return base, None
    import anna_domains
    report = await anna_domains.discover()
    return report.get('selected'), report


async def search_auto(query, base, limit, headed, wait_seconds, manual_captcha, text_captcha_ocr):
    chosen, domain_report = await resolve_base(base)
    if not chosen:
        return {'status': domain_report['status'], 'domain_check': domain_report}
    result = await run(books.anna_url(query, chosen), limit=limit, headed=headed,
                       wait_seconds=wait_seconds, manual_captcha=manual_captcha, text_captcha_ocr=text_captcha_ocr)
    result['base'] = chosen
    # Une restriction du catalogue n'entraîne jamais une nouvelle tentative sur un miroir.
    return result


def search(query, base='auto', limit=10, headed=False, wait_seconds=None, manual_captcha=False, text_captcha_ocr=False):
    if not query.strip() or not 1 <= limit <= 25:
        raise ValueError('Requête et limite de 1 à 25 attendues')
    wait_seconds = wait_seconds if wait_seconds is not None else (600 if manual_captcha else 90 if text_captcha_ocr else 45)
    return asyncio.run(search_auto(query, base, limit, headed, wait_seconds, manual_captcha, text_captcha_ocr))


async def download_auto(target, base, headed, wait_seconds, metadata, manual_captcha, text_captcha_ocr):
    if metadata.get('rights') not in books.RIGHTS or not metadata.get('evidence', '').strip():
        raise ValueError('Droits et provenance requis avant le parcours de téléchargement')
    chosen, domain_report = await resolve_base(base)
    if not chosen:
        return {'status': domain_report['status'], 'domain_check': domain_report}
    if base == 'auto' and target.startswith('https://'):
        supplied = urlsplit(target)
        normalize_target(target, 'https://' + (supplied.hostname or ''))
        target = supplied.path.rsplit('/', 1)[-1]
    url = normalize_target(target, chosen)
    result = await run(url, metadata=metadata, headed=headed, wait_seconds=wait_seconds,
                       manual_captcha=manual_captcha, text_captcha_ocr=text_captcha_ocr)
    result['base'] = chosen
    return result


def download(target, base='auto', headed=False, wait_seconds=None, manual_captcha=False, text_captcha_ocr=False, **metadata):
    wait_seconds = wait_seconds if wait_seconds is not None else (600 if manual_captcha else 180)
    return asyncio.run(download_auto(target, base, headed, wait_seconds, metadata, manual_captcha, text_captcha_ocr))


async def session(base='auto', idle_seconds=600, text_captcha_ocr=False):
    """Plusieurs commandes sur stdin, un seul navigateur ; aucun cookie enregistré."""
    import json

    from playwright.async_api import async_playwright
    chosen, domain_report = await resolve_base(base)
    if not chosen:
        print(json.dumps({'status': domain_report['status'], 'domain_check': domain_report}), flush=True)
        return
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        context.set_default_timeout(10000)
        print(json.dumps({'status': 'session_ready', 'base': chosen, 'idle_seconds': idle_seconds}), flush=True)
        try:
            # Le terminal ne doit pas garder un thread readline bloqué après expiration.
            import selectors
            selector = selectors.DefaultSelector()
            selector.register(sys.stdin, selectors.EVENT_READ)
            try:
                while True:
                    ready = await asyncio.to_thread(selector.select, idle_seconds)
                    if not ready:
                        print(json.dumps({'status': 'session_idle_closed'}), flush=True)
                        break
                    line = sys.stdin.readline()
                    if not line:
                        break
                    try:
                        command = json.loads(line)
                        if command.get('action') == 'exit':
                            break
                        if command.get('action') not in ('search', 'download'):
                            raise ValueError('Action search, download ou exit attendue')
                        metadata = command.get('metadata') if command['action'] == 'download' else None
                        if command['action'] == 'download':
                            if not metadata or metadata.get('rights') not in books.RIGHTS or not metadata.get('evidence', '').strip():
                                raise ValueError('Droits et provenance requis')
                            target = normalize_target(command['target'], chosen)
                        else:
                            if not str(command.get('query', '')).strip():
                                raise ValueError('Requête attendue')
                            target = books.anna_url(command['query'], chosen)
                        # Conserver les cookies seulement en mémoire ; les anciens onglets restent visibles
                        # jusqu'à l'ouverture du suivant, puis sont fermés sans exporter leur état.
                        previous = list(context.pages)
                        async with asyncio.timeout(600):
                            result = await drive(context, target, metadata, min(25, max(1, command.get('limit', 10))),
                                                 manual_captcha=True, text_captcha_ocr=text_captcha_ocr)
                        print(json.dumps(result, ensure_ascii=False), flush=True)
                        for page in previous:
                            if not page.is_closed():
                                await page.close()
                    except TimeoutError:
                        print(json.dumps({'status': 'waiting_timeout'}), flush=True)
                    except Exception:
                        print(json.dumps({'status': 'invalid_command_or_browser_error'}), flush=True)
            finally:
                selector.close()
        finally:
            await context.close()
            await browser.close()
