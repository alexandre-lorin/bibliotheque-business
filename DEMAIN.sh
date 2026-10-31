#!/bin/sh
set -eu
biblio_dir='/home/toubi/01 - Dev/bibliotheque-business'
exec "$biblio_dir/.venv/bin/python" "$biblio_dir/activer.py" --apply
