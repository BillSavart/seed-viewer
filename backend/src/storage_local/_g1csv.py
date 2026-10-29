from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from globals import Global
import os
from archive_storage import archive_ready

router = APIRouter()


@router.get("/")
def g1csv(csvpath: str = None, random: bool = False):
    """Serve G1 robot animation CSV files."""
    if os.environ.get('BONES_ARCHIVE_ROOT') and not archive_ready('g1'):
        return JSONResponse(status_code=503, content={"error": "G1 動作庫正在準備中；目前可先觀看 SOMA 動作。"})

    assert csvpath is not None or random is not None, "Either csvpath or random must be provided."

    if random:
        move = Global.metadata.sample(n=1)
        filename = move.index[0]
        move = move.iloc[0].to_dict()
        move['filename'] = filename
    else:
        if csvpath not in Global.metadata.index:
            return JSONResponse(
                status_code=404, content={"error": f"move '{csvpath}' not found in metadata."}
            )
        move = Global.metadata.loc[csvpath].to_dict()
        move['filename'] = csvpath

    path = move["move_g1_path"]
    if not path or (isinstance(path, float) and path != path):  # Check for NaN
        return JSONResponse(
            status_code=404, content={"error": f"No G1 CSV path available for this move."}
        )

    content = Global.read_file(path)
    if content is None:
        return JSONResponse(
            status_code=404, content={"error": f"G1 CSV file not found: {path}"}
        )

    name = Path(path).stem

    return {
        "name": name,
        "csv": content,
    }
