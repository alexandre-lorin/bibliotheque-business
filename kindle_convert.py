#!/usr/bin/env python3
"""Worker isolé : déballer un MOBI/AZW3 non chiffré en EPUB/HTML/PDF."""
import contextlib
import os
import shutil
import sys
from pathlib import Path

import mobi


def main():
    source, destination = map(Path, sys.argv[1:3])
    folder = None
    try:
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink):
            folder, converted = mobi.extract(str(source))
        converted = Path(converted)
        if converted.suffix.lower() not in ('.epub', '.html', '.pdf'):
            raise ValueError('Format de sortie inattendu')
        if converted.stat().st_size > 80_000_000:
            raise ValueError('Conversion trop volumineuse')
        shutil.copyfile(converted, destination.with_suffix(converted.suffix.lower()))
    finally:
        if folder:
            shutil.rmtree(folder)


if __name__ == '__main__':
    main()
