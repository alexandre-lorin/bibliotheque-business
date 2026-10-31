#!/usr/bin/env python3
"""Activation globale explicite, à lancer dans le terminal habituel de Toubi."""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def install_skills(destination):
    source = ROOT.parent / 'codex-skills' / 'skills'
    reports = []
    for name in ('toubi-humanizer', 'toubi-bibliotheque'):
        src = source / name
        dst = destination / name
        if dst.is_symlink():
            raise ValueError('Destination symbolique existante : ' + name)
        if dst.exists():
            old = {p.relative_to(dst): p.read_bytes() for p in dst.rglob('*') if p.is_file()}
            new = {p.relative_to(src): p.read_bytes() for p in src.rglob('*') if p.is_file()}
            if old != new:
                raise ValueError('Une autre version existe pour ' + name + '. Elle est conservée ; comparer avant remplacement.')
            reports.append(name + ' déjà installé')
        else:
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
            reports.append(name + ' installé')
    return reports


def register_mcp():
    command = [str(ROOT / '.venv' / 'bin' / 'python'), str(ROOT / 'mcp_server.py')]
    codex = shutil.which('codex') or str(Path.home() / '.local' / 'bin' / 'codex')
    # Lire la configuration globale, pas celle du projet si le terminal est ouvert dans la bibliothèque.
    lookup = subprocess.run([codex, 'mcp', 'get', 'toubi-bibliotheque', '--json'], capture_output=True, text=True, cwd=Path.home())
    if lookup.returncode == 0:
        existing = json.loads(lookup.stdout)
        transport = existing.get('transport', {})
        if transport.get('command') == command[0] and transport.get('args') == command[1:]:
            return 'MCP déjà configuré'
        raise ValueError('Un MCP de même nom existe avec une configuration différente ; configuration conservée.')
    result = subprocess.run([codex, 'mcp', 'add', 'toubi-bibliotheque', '--', *command], capture_output=True, text=True, cwd=Path.home())
    if result.returncode:
        raise ValueError('Codex n’a pas pu enregistrer le MCP. Vérifier l’accès au dossier de configuration.')
    return 'MCP configuré'


def install_service():
    directory = Path.home() / '.config' / 'systemd' / 'user'
    destination = directory / 'toubi-bibliotheque.service'
    # Les guillemets systemd protègent les espaces des chemins ; aucun shell exécuté.
    def quoted(path):
        return '"' + str(path).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'
    content = ('[Unit]\nDescription=Indexation de la bibliothèque de Toubi\n\n[Service]\nType=simple\n'
               f'ExecStart={quoted(ROOT / ".venv/bin/python")} {quoted(ROOT / "sync.py")} --watch --interval 60\n'
               'Restart=on-failure\nRestartSec=15\nNice=10\n\n[Install]\nWantedBy=default.target\n')
    if destination.exists() and destination.read_text() != content:
        raise ValueError('Un service différent existe ; il est conservé.')
    directory.mkdir(parents=True, exist_ok=True)
    destination.write_text(content)
    for args in (['daemon-reload'], ['enable', '--now', 'toubi-bibliotheque.service']):
        done = subprocess.run(['systemctl', '--user', *args], capture_output=True)
        if done.returncode:
            raise ValueError('Service écrit mais activation systemd non terminée ; voir systemctl --user status toubi-bibliotheque.')
    return 'Synchronisation automatique activée à chaque session utilisateur'


def install_command():
    destination = Path.home() / '.local' / 'bin' / 'toubi-biblio'
    content = ('#!/bin/sh\nexec ' + shlex.quote(str(ROOT / '.venv/bin/python')) + ' '
               + shlex.quote(str(ROOT / 'rag.py')) + ' "$@"\n')
    if destination.is_symlink() or (destination.exists() and destination.read_text() != content):
        raise ValueError('Une commande toubi-biblio différente existe ; elle est conservée.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content)
    destination.chmod(0o755)
    return 'Commande toubi-biblio installée dans ~/.local/bin'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true', help='Installer les deux skills, enregistrer le MCP et activer la synchronisation')
    a = p.parse_args()
    if not a.apply:
        print('Préparé : deux skills globaux, MCP stdio local, service de synchronisation toutes les 60 secondes.\n'
              'Les originaux et les configurations existantes différentes sont conservés.\n'
              'Pour appliquer : .venv/bin/python activer.py --apply')
        return 0
    try:
        if not (ROOT / '.venv' / 'bin' / 'python').is_file():
            raise ValueError('Environnement Python manquant')
        destination = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
        for message in install_skills(destination):
            print(message, flush=True)
        print(register_mcp(), flush=True)
        print(install_command(), flush=True)
        print(install_service(), flush=True)
        print('Activation terminée. Ouvrir un nouveau tour Codex, puis vérifier /mcp.')
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        print('Les étapes déjà réussies sont conservées ; une relance reconnaît les configurations identiques.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
