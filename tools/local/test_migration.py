"""Exercise real copy, extraction, verification and source cleanup on tiny fixtures."""
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('migrate.py')

class MigrationTest(unittest.TestCase):
    def fixture(self, root):
        spec = importlib.util.spec_from_file_location('migration_fixture', SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.BASE = root
        mod.SOURCE = root / 'bones-seed'
        mod.DEST = root / 'external/bones-seed'
        mod.STATUS = root / 'status.json'
        mod.SOURCE.mkdir()
        metadata = mod.SOURCE / 'metadata'
        metadata.mkdir()
        row = {}
        content = b'fixture motion data\n'
        for name, column, folder, extension in [
            ('soma_uniform', 'move_soma_uniform_path', 'bvh', 'bvh'),
            ('soma_proportional', 'move_soma_proportional_path', 'bvh', 'bvh'),
            ('g1', 'move_g1_path', 'csv', 'csv')
        ]:
            relative = f'{name}/{folder}/240918/test__A001.{extension}'
            row[column] = relative
            archive = mod.SOURCE / (name + '.tar.gz')
            with tarfile.open(archive, 'w:gz') as tar:
                member = tarfile.TarInfo(relative)
                member.size = len(content)
                tar.addfile(member, io.BytesIO(content))
            cache = mod.SOURCE / '.cache/huggingface/download'
            cache.mkdir(parents=True, exist_ok=True)
            (cache / (archive.name + '.metadata')).write_text('revision\n' + hashlib.sha256(archive.read_bytes()).hexdigest() + '\n0\n')
        with (metadata / 'seed_metadata_v004.csv').open('w') as out:
            writer = csv.DictWriter(out, fieldnames=list(row))
            writer.writeheader()
            writer.writerow(row)
        return mod, row, content

    def test_verified_migration_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(Path, 'is_mount', return_value=True):
            mod, row, content = self.fixture(Path(folder))
            mod.run()
            self.assertEqual(mod.state['stage'], 'complete')
            self.assertEqual(len(mod.state['completed']), 3)
            self.assertTrue(mod.SOURCE.is_symlink())
            self.assertEqual(mod.SOURCE.resolve(), mod.DEST)
            self.assertFalse((mod.BASE / 'bones-seed.migrated-original').exists())
            for relative in row.values():
                self.assertEqual((mod.DEST / relative).read_bytes(), content)

    def test_wrong_source_hash_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(Path, 'is_mount', return_value=True):
            mod, _, _ = self.fixture(Path(folder))
            cache = mod.SOURCE / '.cache/huggingface/download/soma_uniform.tar.gz.metadata'
            cache.write_text('revision\n' + '0'*64 + '\n0\n')
            with self.assertRaisesRegex(RuntimeError, 'source SHA-256 mismatch'):
                mod.run()
            self.assertFalse(mod.SOURCE.is_symlink())
            self.assertTrue((mod.SOURCE / 'soma_uniform.tar.gz').is_file())

    def test_corrupt_destination_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(Path, 'is_mount', return_value=True):
            mod, _, _ = self.fixture(Path(folder))
            original_open = Path.open
            def corrupt_on_verification(path, mode='r', *args, **kwargs):
                if path == mod.DEST / 'soma_uniform.tar.gz' and mode == 'rb':
                    with original_open(path, 'r+b') as out:
                        out.write(b'BAD')
                return original_open(path, mode, *args, **kwargs)
            with patch.object(Path, 'open', corrupt_on_verification):
                with self.assertRaisesRegex(RuntimeError, 'Destination SHA-256 mismatch'):
                    mod.run()
            self.assertFalse(mod.SOURCE.is_symlink())
            self.assertTrue((mod.SOURCE / 'soma_uniform.tar.gz').is_file())

if __name__ == '__main__':
    unittest.main()
