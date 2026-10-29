# SOMA reference data

`soma-calibration.json` is derived from the local NVIDIA Kimodo assets
`kimodo/assets/skeletons/somaskel77/standard_t_pose_global_offsets_rots.p`,
`joints.p`, `relaxed_hands_rest_pose.npy`, and the SOMA 30/77 joint definitions.
These assets and definitions are distributed with Kimodo under Apache-2.0:
https://github.com/nv-tlabs/kimodo

Quaternion components use Three.js / SciPy order: `[x, y, z, w]`.
Standard joint positions are meters, relative to Hips at the origin.
`G_standard = G_original * inverse(globalOffset)` follows Kimodo's
`kimodo/skeleton/transforms.py`.

`soma-original-hierarchy.bvh` contains only the skeleton declaration extracted
from the local BONES-SEED example. Dataset terms still apply to this reference:
see `../../bones-seed/LICENSE.md`.

`soma-standard-hierarchy.bvh` is the hierarchy section of Kimodo's
`somaskel77_standard_tpose.bvh`.
