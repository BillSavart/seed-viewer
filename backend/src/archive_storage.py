"""Read indexed motion files directly from the verified archives on the SSD."""
import json
import os
from pathlib import Path
import sqlite3
import threading
from contextlib import closing

BASE = Path('/home/imlab/Desktop/Bill')
INDEX = BASE / 'bones-tools/archive-index'
SUPPORTED = {'soma_uniform', 'g1'}
_readers = {}
_lock = threading.RLock()

def archive_ready(name):
    root = os.environ.get('BONES_ARCHIVE_ROOT')
    marker = INDEX / (name + '.ready.json')
    if not root or name not in SUPPORTED or not marker.is_file():
        return False
    identity = json.loads(marker.read_text())
    source = Path(root) / (name + '.tar.gz')
    if not source.is_file():
        return False
    info = source.stat()
    return info.st_size == identity['bytes'] and info.st_mtime_ns == identity['mtime_ns']

def read_archive_file(relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        return None
    name = path.parts[0]
    if not archive_ready(name):
        return None
    with closing(sqlite3.connect(f'file:{INDEX / (name + ".sqlite")}?mode=ro', uri=True)) as database:
        item = database.execute('SELECT offset,size FROM files WHERE path=?', (str(path),)).fetchone()
    if item is None:
        return None
    with _lock:
        if name not in _readers:
            import rapidgzip
            source = Path(os.environ['BONES_ARCHIVE_ROOT']) / (name + '.tar.gz')
            reader = rapidgzip.RapidgzipFile(str(source), parallelization=2)
            reader.import_index(str(INDEX / (name + '.gzindex')))
            _readers[name] = reader
        reader = _readers[name]
        reader.seek(item[0])
        data = reader.read(item[1])
    if len(data) != item[1]:
        raise IOError('Indexed archive returned an incomplete motion')
    return data.decode('utf-8')

def close_archives():
    with _lock:
        for reader in _readers.values():
            reader.close()
        _readers.clear()
