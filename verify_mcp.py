#!/usr/bin/env python3
"""Recette réelle du serveur MCP stdio, sans utiliser de compte ou de modèle payant."""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parent


def decoded(result):
    if result.is_error:
        raise RuntimeError('Erreur du serveur MCP')
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(next(x.text for x in result.content if x.type == 'text'))


async def verify(mode):
    started = time.monotonic()
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / 'mcp_server.py')], cwd='/tmp')
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            expected = {'search_library', 'library_context', 'read_library_document', 'library_status'}
            assert names == expected, names
            found = decoded(await session.call_tool('search_library', {'query': 'conditions prix abonnement annuel', 'mode': mode, 'limit': 4}))
            # Certains SDK enveloppent une sortie dans result ; normaliser sans masquer une erreur.
            if 'results' not in found and 'result' in found:
                found = found['result']
            assert found['results'], found
            first = found['results'][0]
            assert first['status'] != 'reference_seule'
            document = decoded(await session.call_tool('read_library_document', {'document_id': first['document_id'], 'max_chars': 3000}))
            assert document.get('text') or document.get('result', {}).get('text')
            context_result = await session.call_tool('library_context', {'query': 'offre commerciale', 'max_chars': 4000, 'limit': 3})
            assert not context_result.is_error
            status = decoded(await session.call_tool('library_status', {}))
            report = {'transport': 'stdio', 'client': 'SDK MCP réel', 'tools': sorted(names),
                      'mode': mode, 'results': len(found['results']), 'warnings': found['warnings'],
                      'first_document': first['document_id'], 'status': status,
                      'seconds': round(time.monotonic() - started, 3)}
            return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['hybrid', 'lexical'], default='hybrid')
    args = parser.parse_args()
    print(json.dumps(asyncio.run(verify(args.mode)), ensure_ascii=False, indent=2))
