"""Reconnaissance locale de l'image textuelle DDoS-Guard, une seule proposition."""
import asyncio
import json
import os
import re
import time

import books

ROOT = books.ROOT


async def read_image(raw, engine=None):
    engine = engine or os.environ.get('TOUBI_CAPTCHA_OCR_BACKEND', 'auto')
    if engine not in ('auto', 'ddddocr', 'vision'):
        return {'status': 'invalid_ocr_backend'}
    if engine in ('auto', 'vision'):
        import vision_ocr
        prediction = await vision_ocr.recognize(raw)
        if prediction.get('status') == 'predicted' or engine == 'vision':
            return prediction
    interpreter = ROOT / '.venv-ocr' / 'bin' / 'python'
    if not interpreter.is_file():
        return {'status': 'ocr_not_installed'}
    process = await asyncio.create_subprocess_exec(
        str(interpreter), str(ROOT / 'text_ocr_worker.py'),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    try:
        output, _ = await asyncio.wait_for(process.communicate(raw), 30)
        return json.loads(output)
    except (TimeoutError, ValueError):
        process.kill()
        await process.wait()
        return {'status': 'ocr_error'}


async def advance(page, state):
    """Ne journalise ni image, ni réponse, ni cookies ; ne renouvelle pas un défi raté."""
    if state.get('submitted'):
        if time.monotonic() - state['submitted'] < 4:
            return 'ocr_waiting_result'
        return 'ocr_not_accepted'
    if state.get('attempted'):
        return 'ocr_unavailable'
    state.setdefault('started', time.monotonic())
    normalized_title = (await page.title()).casefold().replace('-', '')
    if 'ddosguard' not in normalized_title:
        state['diagnostic'] = 'different_challenge_type'
        return 'ocr_unsupported'
    field = None
    frame = None
    for candidate in page.frames:
        if candidate != page.main_frame:
            element = await candidate.frame_element()
            if not await element.is_visible():
                continue
        fields = candidate.locator('input[name=captcha]:visible')
        if await fields.count() == 1:
            field = fields.first
            frame = candidate
            break
    if field is None:
        if not state.get('bootstrap_clicked'):
            for candidate in page.frames:
                if candidate != page.main_frame and not await (await candidate.frame_element()).is_visible():
                    continue
                labels = candidate.get_by_text(re.compile(
                    r"^(i['’]m not a robot|i am not a robot|je ne suis pas un robot)$", re.I))
                if await labels.count() == 1 and await labels.first.is_visible():
                    await labels.first.click(timeout=5000)
                    state['bootstrap_clicked'] = time.monotonic()
                    return 'ocr_challenge_loading'
            # Ne jamais cliquer un bouton arbitraire : « Show IP address » n'est pas
            # le contrôle de vérification. Le contrôle initial est souvent automatique.
            buttons = page.get_by_role('button', name=re.compile(
                r'^(verify you are human|i am human|start verification|start check|vérifier|continuer)$', re.I))
            if await buttons.count() == 1 and await buttons.first.is_visible():
                await buttons.first.click(timeout=5000)
                state['bootstrap_clicked'] = time.monotonic()
                return 'ocr_challenge_loading'
        if time.monotonic() - state['started'] < 60:
            return 'ocr_challenge_loading'
        state['diagnostic'] = ('text_form_not_visible;bootstrap=' + str(bool(state.get('bootstrap_clicked')))
                               + ';frames=' + str(len(page.frames)))
        return 'ocr_unsupported'
    images = []
    for image in await frame.locator('img:visible').all():
        box = await image.bounding_box()
        if box and 90 <= box['width'] <= 500 and 25 <= box['height'] <= 180:
            images.append(image)
    if len(images) != 1:
        if not images and time.monotonic() - state['started'] < 20:
            return 'ocr_challenge_loading'
        state['diagnostic'] = 'image_count_' + str(len(images))
        return 'ocr_unsupported'
    state['attempted'] = True
    raw = await images[0].screenshot(timeout=3000)
    prediction = await read_image(raw)
    text = prediction.get('text', '')
    if prediction.get('status') not in ('recognized', 'predicted') or not re.fullmatch(r'[A-Za-z0-9]{3,10}', text):
        state['diagnostic'] = prediction.get('status', 'invalid_prediction')
        return 'ocr_unavailable'
    state['models_agreement'] = prediction.get('agreement')
    state['engine'] = prediction.get('engine', 'ddddocr')
    maximum = await field.get_attribute('maxlength')
    if maximum and maximum.isdigit() and len(text) > int(maximum):
        state['diagnostic'] = 'prediction_exceeds_field_length'
        return 'ocr_unavailable'
    submit = frame.locator('button[type=submit],input[type=submit]')
    if await submit.count() != 1:
        state['diagnostic'] = 'submit_count_' + str(await submit.count())
        return 'ocr_unsupported'
    await field.fill(text)
    # Une seule réponse, par le bouton normal du formulaire. Aucun rafraîchissement du défi.
    await submit.click(timeout=5000)
    state['submitted'] = time.monotonic()
    return 'ocr_submitted_once'
