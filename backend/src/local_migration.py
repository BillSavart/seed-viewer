"""Local extraction progress and playable files while migration is running."""
import json
import os
from pathlib import Path
import time
from globals import Global
from archive_storage import archive_ready, INDEX

STATUS = Path('/home/imlab/Desktop/Bill/bones-tools/migration-status.json')
_cached_names = set()
_checked_at = 0

def migration_status():
    if os.environ.get('BONES_ARCHIVE_ROOT'):
        ready = archive_ready('soma_uniform')
        progress = INDEX / 'soma_uniform.status.json'
        status = json.loads(progress.read_text()) if progress.is_file() else {}
        return {'mode': 'internal_ssd', 'stage': 'ready' if ready else 'indexing',
                'files': status.get('files', 0), 'total': len(Global.metadata),
                'soma_ready': ready, 'g1_ready': archive_ready('g1')}
    if STATUS.is_file():
        status = json.loads(STATUS.read_text())
        status['local_preview'] = Global.files_path.endswith('/bones-preview')
        return status
    return {'stage': 'unavailable'}

def playable_moves(moves):
    global _cached_names, _checked_at
    root = Path(Global.files_path)
    if os.environ.get('BONES_ARCHIVE_ROOT'):
        if archive_ready('soma_uniform'):
            return moves
        root = Path('/home/imlab/Desktop/Bill/bones-preview')
    if (root / '.soma_uniform.verified.json').exists() or not STATUS.exists():
        return moves
    if time.monotonic() - _checked_at > 15:
        _cached_names = {
            name[:-4] for _, _, files in os.walk(root / 'soma_uniform/bvh')
            for name in files if name.endswith('.bvh')
        }
        _checked_at = time.monotonic()
    return moves[moves.index.isin(_cached_names)]
