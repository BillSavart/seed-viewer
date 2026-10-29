#!/usr/bin/env python3
"""Run the browser viewer entirely from the internal SSD."""
import os
from pathlib import Path

base = Path('/home/imlab/Desktop/Bill')
data = base / 'bones-seed'
os.environ['DATA_ROOT'] = str(data)
os.environ['DATA_FILES_ROOT'] = str(data)
os.environ['BONES_ARCHIVE_ROOT'] = str(data)
python = str(base / 'seed-viewer/.venv/bin/python')
os.execv(python, [
    python, '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8666'
])
