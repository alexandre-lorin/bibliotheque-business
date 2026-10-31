#!/usr/bin/env python3
"""OCR d'image en local. Python 3.12 isolé ; résultat transmis seulement sur le pipe."""
import io
import json
import re
import string
import sys
from collections import Counter


def recognize(raw):
    import ddddocr
    import onnxruntime
    from PIL import Image, ImageEnhance, ImageOps
    onnxruntime.disable_telemetry_events()
    if len(raw) > 2_000_000:
        return {'status': 'image_too_large'}
    image = Image.open(io.BytesIO(raw))
    if max(image.size) > 1500:
        return {'status': 'image_too_large'}
    image = image.convert('RGB')
    variants = [image, ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(2)]
    predictions = []
    for beta in (False, True):
        model = ddddocr.DdddOcr(show_ad=False, beta=beta)
        model.set_ranges(string.ascii_letters + string.digits)
        values = []
        for variant in variants:
            buffer = io.BytesIO()
            variant.save(buffer, format='PNG')
            text = model.classification(buffer.getvalue()).strip()
            if re.fullmatch(r'[A-Za-z0-9]{3,10}', text):
                values.append(text)
        predictions.append(values)
    # Une hypothèse bornée : accord des modèles si possible, sinon meilleur vote.
    # Le serveur juge la proposition ; aucun résultat n'est présenté comme certain.
    common = set(predictions[0]).intersection(predictions[1])
    counts = Counter(value for values in predictions for value in values)
    if not counts:
        return {'status': 'recognition_ambiguous'}
    eligible = common or set(counts)
    preferred = predictions[0][0] if predictions[0] else next(iter(counts))
    text = max(eligible, key=lambda value: (counts[value], value == preferred, value))
    agreement = text in common
    return {'status': 'recognized' if agreement else 'predicted', 'text': text, 'engines': 2,
            'agreement': agreement, 'votes': counts[text]}


if __name__ == '__main__':
    try:
        answer = recognize(sys.stdin.buffer.read(2_000_001))
    except Exception:
        answer = {'status': 'ocr_error'}
    # Le parent capture ce pipe : ne pas lancer ce worker avec une image privée dans un terminal.
    sys.stdout.write(json.dumps(answer))
