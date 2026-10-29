#!/usr/bin/env python3
"""Move SEED to Transcend, validating archives and extracted metadata paths."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import time
import traceback

BASE = Path('/home/imlab/Desktop/Bill')
SOURCE = BASE / 'bones-seed'
DEST = Path('/media/imlab/Transcend/Bill/bones-seed')
STATUS = BASE / 'bones-tools/migration-status.json'
state = {'stage': 'starting', 'completed': [], 'destination': str(DEST)}

def update(**values):
    state.update(values, updated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    temp = STATUS.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2))
    temp.replace(STATUS)

class CopyReader:
    def __init__(self, source, target):
        self.source, self.target = source, target
        self.hash = hashlib.sha256()
        self.count, self.last, self.last_flush = 0, 0, 0
    def read(self, size=-1):
        data = self.source.read(size)
        self.target.write(data)
        self.hash.update(data)
        self.count += len(data)
        if self.count - self.last_flush >= 256*1024*1024:
            self.target.flush()
            os.fsync(self.target.fileno())
            self.last_flush = self.count
        if time.monotonic() - self.last > 10:
            update(compressed_bytes=self.count)
            self.last = time.monotonic()
        return data

def run():
    if (BASE / 'bones-tools/HARDWARE_HOLD').exists():
        raise RuntimeError('Transcend 曾發生寫入 I/O 錯誤；需先確認硬碟／連線健康後再解除 HARDWARE_HOLD。')
    if not Path('/media/imlab/Transcend').is_mount():
        raise RuntimeError('Transcend is not mounted')
    if SOURCE.is_symlink():
        raise RuntimeError('Dataset already migrated; inspect status before rerunning')
    DEST.mkdir(parents=True, exist_ok=True)
    # Preserve all small original files, including provenance and download metadata.
    update(stage='copying_metadata')
    for src in SOURCE.rglob('*'):
        if src.is_file() and not src.name.endswith('.tar.gz'):
            dst = DEST / src.relative_to(SOURCE)
            dst.parent.mkdir(parents=True, exist_ok=True)
            expected_hash = hashlib.sha256(src.read_bytes()).digest()
            if dst.is_file() and dst.stat().st_size == src.stat().st_size and hashlib.sha256(dst.read_bytes()).digest() == expected_hash:
                continue
            temp = dst.with_name(dst.name + '.copying')
            shutil.copy2(src, temp)
            with temp.open('rb') as copied:
                os.fsync(copied.fileno())
            if expected_hash != hashlib.sha256(temp.read_bytes()).digest():
                raise RuntimeError(f'Copy mismatch: {src}')
            temp.replace(dst)
    for name in ['soma_uniform', 'soma_proportional', 'g1']:
        archive = name + '.tar.gz'
        marker = DEST / ('.' + name + '.verified.json')
        if marker.exists():
            state['completed'].append(name)
            continue
        src = SOURCE / archive
        dst = DEST / archive
        expected = (SOURCE / '.cache/huggingface/download' / (archive + '.metadata')).read_text().splitlines()[1]
        total = src.stat().st_size
        update(stage='copying_and_extracting', archive=archive, compressed_total=total,
               compressed_bytes=0, extracted_files=0, extracted_bytes=0)
        count, extracted_size = 0, 0
        partial = dst.with_suffix(dst.suffix + '.partial')
        # Batch archive writes to avoid seeking between archive and extracted
        # files every few megabytes on the external mechanical disk.
        with src.open('rb', buffering=4*1024*1024) as inp, partial.open('wb', buffering=256*1024*1024) as out:
            reader = CopyReader(inp, out)
            with tarfile.open(fileobj=reader, mode='r|gz', bufsize=1024*1024) as tar:
                for member in tar:
                    rel = Path(member.name)
                    if rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0] != name:
                        raise RuntimeError(f'Unexpected archive path: {member.name}')
                    path = DEST / rel
                    if member.isdir():
                        path.mkdir(parents=True, exist_ok=True)
                        continue
                    if not member.isfile():
                        raise RuntimeError(f'Unexpected nonregular member: {member.name}')
                    if count % 1000 == 0 and shutil.disk_usage(DEST).free < max(10*1024**3, member.size*2):
                        raise RuntimeError('Low disk space; source preserved')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    temp = path.with_name(path.name + '.partial')
                    with tar.extractfile(member) as data, temp.open('wb') as target:
                        shutil.copyfileobj(data, target, 1024*1024)
                        # Keep writes sequential on NTFS mechanical disks instead
                        # of accumulating many gigabytes of scattered dirty data.
                        target.flush()
                        os.fsync(target.fileno())
                    if temp.stat().st_size != member.size:
                        raise RuntimeError(f'Incomplete extracted file: {path}')
                    temp.replace(path)
                    count += 1
                    extracted_size += member.size
                    state.update(extracted_files=count, extracted_bytes=extracted_size)
            while reader.read(4*1024*1024):
                pass
            out.flush()
            os.fsync(out.fileno())
            if reader.count != total or reader.hash.hexdigest() != expected:
                raise RuntimeError(f'Archive source SHA-256 mismatch: {archive}')
        partial.replace(dst)
        update(stage='verifying_destination', compressed_bytes=total)
        digest = hashlib.sha256()
        with dst.open('rb', buffering=4*1024*1024) as check:
            while chunk := check.read(4*1024*1024):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError(f'Destination SHA-256 mismatch: {archive}')
        # Ensure every metadata row has a full extracted motion file.
        import csv
        column = {'soma_uniform':'move_soma_uniform_path', 'soma_proportional':'move_soma_proportional_path', 'g1':'move_g1_path'}[name]
        with (DEST / 'metadata/seed_metadata_v004.csv').open() as metadata:
            rows = list(csv.DictReader(metadata))
        missing = [row[column] for row in rows if not (DEST / row[column]).is_file()]
        if missing:
            raise RuntimeError(f'{name}: {len(missing)} missing metadata paths; first {missing[:3]}')
        record = {'archive':archive, 'sha256':expected, 'compressed_bytes':total,
                  'extracted_files':count, 'extracted_bytes':extracted_size, 'metadata_rows':len(rows)}
        marker.write_text(json.dumps(record, indent=2))
        state['completed'].append(name)
        update(stage='archive_verified', last_verified=record)
        print(json.dumps(record), flush=True)
    # Only remove originals after all three archives and all metadata paths verify.
    update(stage='switching_path')
    original_files = [p for p in SOURCE.rglob('*') if p.is_file()]
    for src in original_files:
        dst = DEST / src.relative_to(SOURCE)
        if not dst.is_file() or src.stat().st_size != dst.stat().st_size:
            raise RuntimeError(f'Original not safely copied: {src}')
    old = BASE / 'bones-seed.migrated-original'
    if old.exists():
        raise RuntimeError(f'Unexpected existing backup path: {old}')
    SOURCE.rename(old)
    try:
        SOURCE.symlink_to(DEST, target_is_directory=True)
    except Exception:
        old.rename(SOURCE)
        raise
    shutil.rmtree(old)
    update(stage='complete')

if __name__ == '__main__':
    lock = (BASE / 'bones-tools/migration.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        run()
    except BaseException as error:
        update(stage='failed', error=str(error))
        traceback.print_exc()
        raise
