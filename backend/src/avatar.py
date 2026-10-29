"""Local VRM asset and Kimodo-SOMA NPZ import (no model inference required)."""
from io import BytesIO
from pathlib import Path
import json
import zipfile

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse

router = APIRouter()
ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "shared"
CALIBRATION = json.loads((SHARED / "soma-calibration.json").read_text())


@router.get("/avatar")
def avatar():
    path = ROOT.parent / "AvatarSample_M.vrm"
    if not path.is_file():
        raise HTTPException(404, "找不到 AvatarSample_M.vrm")
    return FileResponse(path, media_type="model/gltf-binary")


def _global(local, parents):
    result = np.empty_like(local)
    for j, parent in enumerate(parents):
        result[:, j] = local[:, j] if parent < 0 else result[:, parent] @ local[:, j]
    return result


def _local(global_rots, parents):
    result = np.empty_like(global_rots)
    for j, parent in enumerate(parents):
        result[:, j] = global_rots[:, j] if parent < 0 else global_rots[:, parent].swapaxes(-1, -2) @ global_rots[:, j]
    return result


def npz_to_bvh(content: bytes, fps: float):
    """Convert 30/77-joint canonical SOMA output to BONES-SEED BVH conventions."""
    with zipfile.ZipFile(BytesIO(content)) as archive:
        if sum(item.file_size for item in archive.infolist()) > 128 * 1024 * 1024:
            raise ValueError("NPZ 解壓後超過 128 MB，請使用較短的動作。")
    with np.load(BytesIO(content), allow_pickle=False) as data:
        key = "local_rot_mats" if "local_rot_mats" in data else "global_rot_mats"
        if key not in data:
            raise ValueError("NPZ 需要 local_rot_mats 或 global_rot_mats。")
        rots = np.asarray(data[key], dtype=np.float64)
        if rots.ndim == 5 and rots.shape[0] == 1:
            rots = rots[0]
        if rots.ndim != 4 or rots.shape[-2:] != (3, 3) or rots.shape[1] not in (30, 77):
            raise ValueError("只支援 Kimodo-SOMA 的 30 或 77 關節旋轉矩陣。")
        count, joints = rots.shape[:2]
        if not 2 <= count <= 20000 or not np.isfinite(rots).all():
            raise ValueError("動作影格數或旋轉數值無效。")
        names = CALIBRATION["names30"] if joints == 30 else CALIBRATION["names"]
        parents = CALIBRATION["parents30"] if joints == 30 else CALIBRATION["parents"]
        local = rots if key == "local_rot_mats" else _local(rots, parents)
        if joints == 30:
            expanded = np.broadcast_to(np.asarray(CALIBRATION["relaxedLocalMatrices"]), (count, 77, 3, 3)).copy()
            for j, name in enumerate(names):
                expanded[:, CALIBRATION["names"].index(name)] = local[:, j]
            local = expanded
        if "root_positions" in data:
            root = np.asarray(data["root_positions"], dtype=np.float64)
        elif "posed_joints" in data:
            posed = np.asarray(data["posed_joints"], dtype=np.float64)
            if posed.ndim == 4 and posed.shape[0] == 1:
                posed = posed[0]
            root = posed[:, 0]
        else:
            raise ValueError("NPZ 需要 root_positions 或 posed_joints。")
        if root.ndim == 3 and root.shape[0] == 1:
            root = root[0]
        if root.shape != (count, 3) or not np.isfinite(root).all():
            raise ValueError("根部位移的影格數或數值無效。")

    # Kimodo's from_standard_tpose: G_original = G_standard @ offset.
    q = np.asarray(CALIBRATION["globalOffsets"])
    x, y, z, w = q.T
    offsets = np.stack([
        1 - 2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w),
        2*(x*y+z*w), 1 - 2*(x*x+z*z), 2*(y*z-x*w),
        2*(x*z-y*w), 2*(y*z+x*w), 1 - 2*(x*x+y*y),
    ], axis=-1).reshape(77, 3, 3)
    original = _local(_global(local, CALIBRATION["parents"]) @ offsets, CALIBRATION["parents"])
    # Intrinsic ZYX Euler angles, matching BVH CHANNELS order.
    pitch = np.arcsin(np.clip(-original[..., 2, 0], -1, 1))
    yaw = np.arctan2(original[..., 1, 0], original[..., 0, 0])
    roll = np.arctan2(original[..., 2, 1], original[..., 2, 2])
    singular = np.abs(np.cos(pitch)) < 1e-7
    yaw = np.where(singular, np.arctan2(-original[..., 0, 1], original[..., 1, 1]), yaw)
    roll = np.where(singular, 0, roll)
    eulers = np.rad2deg(np.stack([yaw, pitch, roll], axis=-1))
    values = np.concatenate([np.zeros((count, 6)), root * 100, eulers.reshape(count, -1)], axis=1)
    buffer = BytesIO()
    np.savetxt(buffer, values, fmt="%.6f")
    hierarchy = (SHARED / "soma-original-hierarchy.bvh").read_text()
    return hierarchy + f"MOTION\nFrames: {count}\nFrame Time: {1/fps:.10f}\n" + buffer.getvalue().decode()


@router.post("/motion/import-npz")
async def import_npz(file: UploadFile = File(...), fps: float = Query(30, ge=1, le=240)):
    content = await file.read(32 * 1024 * 1024 + 1)
    if len(content) > 32 * 1024 * 1024:
        raise HTTPException(413, "NPZ 超過 32 MB，請使用較短的動作。")
    try:
        tree = npz_to_bvh(content, fps)
    except (ValueError, KeyError, IndexError, TypeError, zipfile.BadZipFile) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"name": Path(file.filename or "kimodo.npz").stem, "tree": tree}
