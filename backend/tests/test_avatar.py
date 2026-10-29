"""Round-trip the exported BVH and check unsupported NPZ inputs."""
import io
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from avatar import npz_to_bvh, CALIBRATION


def archive(**values):
    stream = io.BytesIO()
    np.savez(stream, **values)
    return stream.getvalue()


class AvatarImportTests(unittest.TestCase):
    def test_full_soma_canonical_pose_survives_bvh_serialization(self):
        # Nontrivial rotations, including a pitch at gimbal lock.
        rotations = np.broadcast_to(np.eye(3), (3, 77, 3, 3)).copy()
        rotations[1, 0] = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
        rotations[2, 0] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        root = np.array([[0, 1, 0], [1, .8, -2], [2, 1.2, -1]])
        text = npz_to_bvh(archive(local_rot_mats=rotations, root_positions=root), 60)
        lines = text.split('MOTION', 1)[1].strip().splitlines()
        values = np.loadtxt(io.StringIO('\n'.join(lines[2:])))
        self.assertEqual(values.shape, (3, 240))
        np.testing.assert_allclose(values[:, 6:9] / 100, root, atol=1e-7)
        # Reconstruct the Hips rotation from its serialized intrinsic ZYX angles.
        qx, qy, qz, qw = CALIBRATION['globalOffsets'][0]
        offset = np.array([
            [1-2*(qy*qy+qz*qz), 2*(qx*qy-qz*qw), 2*(qx*qz+qy*qw)],
            [2*(qx*qy+qz*qw), 1-2*(qx*qx+qz*qz), 2*(qy*qz-qx*qw)],
            [2*(qx*qz-qy*qw), 2*(qy*qz+qx*qw), 1-2*(qx*qx+qy*qy)],
        ])
        for f, (z, y, x) in enumerate(np.deg2rad(values[:, 9:12])):
            rz = [[np.cos(z), -np.sin(z), 0], [np.sin(z), np.cos(z), 0], [0, 0, 1]]
            ry = [[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]]
            rx = [[1, 0, 0], [0, np.cos(x), -np.sin(x)], [0, np.sin(x), np.cos(x)]]
            canonical = np.array(rz) @ ry @ rx @ offset.T
            np.testing.assert_allclose(canonical, rotations[f, 0], atol=1e-6)

    def test_legacy_30_joint_output_with_only_global_rotations(self):
        rots = np.broadcast_to(np.eye(3), (2, 30, 3, 3))
        joints = np.zeros((2, 30, 3))
        joints[:, 0, 1] = 1
        text = npz_to_bvh(archive(global_rot_mats=rots, posed_joints=joints), 30)
        self.assertIn('Frames: 2', text)
        self.assertEqual(len(text.strip().splitlines()[-1].split()), 240)

    def test_reject_other_skeletons_and_invalid_root(self):
        for count in (22, 34):
            with self.assertRaisesRegex(ValueError, 'Kimodo-SOMA'):
                npz_to_bvh(archive(local_rot_mats=np.zeros((2, count, 3, 3))), 30)
        rots = np.broadcast_to(np.eye(3), (2, 77, 3, 3))
        with self.assertRaisesRegex(ValueError, '根部位移'):
            npz_to_bvh(archive(local_rot_mats=rots, root_positions=np.full((2, 3), np.nan)), 30)


if __name__ == '__main__':
    unittest.main()
