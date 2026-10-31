#!/usr/bin/env python3
"""Repérer les domaines du catalogue. Repli sur panne, jamais sur une restriction."""
import asyncio
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

import anna_browser

ROOT = anna_browser.ROOT
HARD_STOPS = {'captcha_required', 'authentication_required', 'payment_required', 'rate_limited', 'quota_reached', 'access_denied'}
FALLBACK = {'site_unavailable', 'domain_parked', 'not_catalog', 'http_not_found'}


def origin(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or not re.fullmatch(r'annas-archive\.[a-z]{2,16}', p.hostname or '')
            or p.username or p.password or p.port not in (None, 443)):
        raise ValueError('Domaine Anna’s Archive HTTPS attendu')
    return 'https://' + p.hostname


def candidates_from_links(links):
    result = []
    for link in links:
        try:
            candidate = origin(link)
        except ValueError:
            continue
        if candidate not in result:
            result.append(candidate)
    return result


def configuration(root=ROOT):
    value = json.loads((root / 'anna-domains.yaml').read_text())
    value['preferred'] = origin(value['preferred'])
    value['candidates'] = candidates_from_links(value['candidates'])
    value['max_candidates'] = min(12, max(1, value.get('max_candidates', 8)))
    return value


async def page_links(page):
    links = []
    for anchor in await page.locator('a[href]').all():
        href = await anchor.get_attribute('href')
        if href:
            links.append(urljoin(page.url, href))
    return candidates_from_links(links)


async def inspect_page(page, requested, status):
    blocked = await anna_browser.page_block(page, status)
    if blocked:
        return {'base': requested, 'status': blocked, 'announced': []}
    if status == 404:
        return {'base': requested, 'status': 'http_not_found', 'announced': []}
    try:
        final = origin(page.url)
    except ValueError:
        return {'base': requested, 'status': 'untrusted_redirect', 'announced': []}
    # Un titre ressemblant au service ne suffit pas : vérifier aussi le formulaire.
    title = (await page.title()).casefold().replace('’', "'")
    forms = page.locator('form[action*="search"],input[name=q],input[type=search],[role=searchbox]')
    has_search = any([await item.is_visible() for item in await forms.all()])
    available = ("anna's archive" in title or 'annas archive' in title) and has_search
    return {'base': requested, 'final_base': final, 'status': 'homepage_available' if available else 'not_catalog',
            'announced': await page_links(page) if available else []}


async def probe(context, base, _fixture_url=None):
    from playwright.async_api import Error
    page = await context.new_page()
    try:
        response = await page.goto(_fixture_url or base, wait_until='domcontentloaded', timeout=15000)
        return await inspect_page(page, base, response.status if response else None)
    except Error:
        return {'base': base, 'status': 'site_unavailable', 'announced': []}
    finally:
        await page.close()


async def directory_candidates(context, urls):
    found = []
    for url in urls[:2]:
        if not anna_browser.public_target(url):
            continue
        page = await context.new_page()
        try:
            response = await page.goto(url, wait_until='domcontentloaded', timeout=12000)
            if response and response.ok:
                found.extend(await page_links(page))
        except Exception:
            pass
        finally:
            await page.close()
    return list(dict.fromkeys(found))


async def select(preferred, candidates, probe_fn, discover_fn, check_all=False, refresh=False, maximum=8):
    """Orchestration bornée, séparée des requêtes de recherche et téléchargement."""
    queue = list(dict.fromkeys([preferred, *candidates]))
    checked = []
    announcements = []
    selected = None
    selection_block = None
    discovered = False
    if refresh:
        queue.extend(x for x in await discover_fn() if x not in queue)
        discovered = True
    while len(checked) < maximum:
        if not queue:
            if discovered:
                break
            queue.extend(x for x in await discover_fn() if x not in {r['base'] for r in checked})
            discovered = True
            if not queue:
                break
        base = queue.pop(0)
        if base in {r['base'] for r in checked}:
            continue
        report = await probe_fn(base)
        checked.append(report)
        announcements.extend(report.get('announced', []))
        queue.extend(x for x in report.get('announced', []) if x not in queue and x not in {r['base'] for r in checked})
        if selected is None and selection_block is None:
            if report['status'] == 'homepage_available':
                selected = report.get('final_base', base)
            elif report['status'] not in FALLBACK:
                selection_block = report['status']
        if not check_all and (selected or selection_block):
            break
    return {'selected': selected, 'selection_block': selection_block,
            'status': 'homepage_available' if selected else selection_block or 'no_available_domain',
            'checked': checked, 'announced_candidates': list(dict.fromkeys(announcements)),
            'notice': 'Accueil vérifié uniquement ; la recherche ou le téléchargement peut encore demander un CAPTCHA. Aucun essai de téléchargement n’est rejoué.'}


async def discover(check_all=False, refresh=False, root=ROOT):
    from playwright.async_api import async_playwright
    config = configuration(root)
    cache_path = root / 'data' / 'anna-domains-state.json'
    cached = []
    if cache_path.exists():
        old = json.loads(cache_path.read_text())
        cached = candidates_from_links(old.get('announced_candidates', []))
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=False)
        context.set_default_timeout(3000)
        try:
            async def guard(route):
                if anna_browser.public_target(route.request.url):
                    await route.continue_()
                else:
                    await route.abort()
            await context.route('**/*', guard)
            result = await select(config['preferred'], [*config['candidates'], *cached],
                                  lambda base: probe(context, base),
                                  lambda: directory_candidates(context, config['discovery_sources']),
                                  check_all, refresh, config['max_candidates'])
        finally:
            await context.close()
            await browser.close()
    result['checked_at'] = datetime.now(timezone.utc).isoformat()
    cache_path.parent.mkdir(exist_ok=True)
    cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def check(refresh=False):
    return asyncio.run(discover(check_all=True, refresh=refresh))
