#!/usr/bin/env python3
"""Index a verified motion archive for browser playback without unpacking it."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tarfile
import time
import rapidgzip
import pandas as pd

BASE = Path('/home/imlab/Desktop/Bill')
DATA = BASE / 'bones-seed'
INDEX = BASE / 'bones-tools/archive-index'

def build(name):
    INDEX.mkdir(exist_ok=True)
    source = DATA / (name + '.tar.gz')
    integrity = json.loads((BASE / 'bones-tools/source-integrity.json').read_text())
    record = integrity['archives'][source.name]
    if not record['matches'] or source.stat().st_size != record['bytes']:
        raise RuntimeError('Archive must pass SHA-256 verification before indexing')
    if shutil.disk_usage(INDEX).free < 15*1024**3:
        raise RuntimeError('Not enough free space for archive indexes')
    status = {'archive': name, 'stage': 'indexing', 'files': 0, 'compressed_total': source.stat().st_size}
    status_file = INDEX / (name + '.status.json')
    def update(**values):
        status.update(values, updated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        temp = status_file.with_suffix('.tmp')
        temp.write_text(json.dumps(status, indent=2))
        temp.replace(status_file)
    update()
    database = INDEX / (name + '.sqlite.partial')
    database.unlink(missing_ok=True)
    connection = sqlite3.connect(database)
    connection.execute('CREATE TABLE files(path TEXT PRIMARY KEY, offset INTEGER, size INTEGER)')
    count, last = 0, 0
    try:
        with rapidgzip.RapidgzipFile(str(source), parallelization=12) as reader:
            with tarfile.open(fileobj=reader, mode='r|', bufsize=4*1024*1024) as archive:
                for member in archive:
                    path = Path(member.name)
                    if path.is_absolute() or '..' in path.parts or path.parts[0] != name:
                        raise RuntimeError('Unexpected archive member path')
                    if not member.isfile():
                        continue
                    connection.execute('INSERT INTO files VALUES(?,?,?)', (member.name, member.offset_data, member.size))
                    count += 1
                    if time.monotonic() - last > 5:
                        connection.commit()
                        update(files=count, compressed_bytes=reader.tell_compressed() // 8, uncompressed_bytes=reader.tell())
                        last = time.monotonic()
            while reader.read(4*1024*1024):
                pass
            gzip_index = INDEX / (name + '.gzindex.partial')
            reader.export_index(str(gzip_index))
        connection.commit()
        column = {'soma_uniform':'move_soma_uniform_path','g1':'move_g1_path'}[name]
        expected = pd.read_parquet(DATA / 'metadata/seed_metadata_v004.parquet', columns=[column])[column]
        indexed = {row[0] for row in connection.execute('SELECT path FROM files')}
        missing = set(expected) - indexed
        if missing:
            raise RuntimeError(f'{len(missing)} metadata paths absent from archive')
        connection.close()
        gzip_index.replace(INDEX / (name + '.gzindex'))
        database.replace(INDEX / (name + '.sqlite'))
        identity = {'archive': name, 'sha256': record['actual_sha256'], 'bytes': source.stat().st_size,
                    'mtime_ns': source.stat().st_mtime_ns, 'files': count, 'metadata_paths':len(expected)}
        (INDEX / (name + '.ready.json')).write_text(json.dumps(identity,indent=2))
        update(stage='ready', files=count, compressed_bytes=source.stat().st_size)
        print(json.dumps(identity),flush=True)
    except BaseException as error:
        update(stage='failed', error=str(error))
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', choices=['soma_uniform','g1'])
    build(parser.parse_args().archive)
