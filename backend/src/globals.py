from loguru import logger
import json
import os
from pathlib import Path
import pandas as pd


class Global:

    metadata: pd.DataFrame = None
    files_path: str = None
    openapi_disable: bool = False
    temporal_labels_data: dict = None

    @staticmethod
    def initialize():
        logger.info("initializing globals...")

        Global.openapi_disable = True

        data_root = os.environ.get("DATA_ROOT", "/mnt/bones")
        metadata_dir = os.path.join(data_root, "metadata/")

        metadata_path = Global._find_local_metadata_file(metadata_dir)
        print(f"loading metadata from: {metadata_path}")
        Global.metadata = Global._load_metadata_from_path(metadata_path)

        files_path = os.environ.get("DATA_FILES_ROOT", os.path.join(data_root, "files"))
        Global.files_path = files_path
        print(f"files path set to: {files_path}")

        tl_path = Global._find_local_temporal_labels_file(metadata_dir)
        Global.temporal_labels_data = Global._load_temporal_labels_from_path(tl_path) if tl_path else {}

        logger.info("globals initialized!")

    @staticmethod
    def read_file(relative_path: str) -> str | None:
        """Read a text file from the local filesystem.

        Args:
            relative_path: Path relative to the files root (e.g. "anims_uniform/BVH/file.bvh")

        Returns:
            File content as string, or None if not found.
        """
        full_path = os.path.join(Global.files_path, relative_path)
        if not Path(full_path).is_file():
            from archive_storage import read_archive_file
            content = read_archive_file(relative_path)
            if content is not None:
                return content
            preview = Path('/home/imlab/Desktop/Bill/bones-preview') / relative_path
            if preview.is_file():
                return preview.read_text()
            return None
        with open(full_path, "r") as f:
            return f.read()

    # --- Metadata loading ---

    @staticmethod
    def _load_metadata_from_path(path: str) -> pd.DataFrame:
        """Load metadata from parquet file."""
        logger.info(f"Loading metadata from: {path}")
        df = pd.read_parquet(path)

        df = df.set_index('filename')

        logger.info(f"Loaded metadata: {len(df)} rows, index='{df.index.name}'")
        return df

    @staticmethod
    def _find_local_metadata_file(metadata_dir: str) -> str:
        """Find the .parquet metadata file in the metadata directory."""
        if not os.path.isdir(metadata_dir):
            raise FileNotFoundError(f"Metadata directory not found: {metadata_dir}")

        candidates = [f for f in os.listdir(metadata_dir) if f.endswith('.parquet') and not f.startswith('._')]
        candidates.sort()
        if candidates:
            return os.path.join(metadata_dir, candidates[0])

        raise FileNotFoundError(f"No .parquet metadata file found in {metadata_dir}")

    # --- Temporal labels ---

    @staticmethod
    def _find_local_temporal_labels_file(metadata_dir: str) -> str | None:
        """Find temporal labels JSONL file in the metadata directory."""
        if os.path.isdir(metadata_dir):
            for f in sorted(os.listdir(metadata_dir)):
                if f.endswith('.jsonl') and not f.startswith('._'):
                    return os.path.join(metadata_dir, f)

        logger.warning(f"No temporal labels JSONL found in {metadata_dir}")
        return None

    @staticmethod
    def _load_temporal_labels_from_path(path: str) -> dict:
        """Load temporal label events from a local JSONL file."""
        if not os.path.isfile(path):
            logger.warning(f"Temporal labels file not found: {path}")
            return {}
        with open(path, "r") as f:
            return Global._parse_temporal_labels(f.read())

    @staticmethod
    def _parse_temporal_labels(text: str) -> dict:
        """Parse temporal labels from JSONL text."""
        data = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            data[entry["filename"]] = entry["events"]
        logger.info(f"Loaded temporal labels for {len(data)} moves")
        return data

    @staticmethod
    def deinitialize():
        from archive_storage import close_archives
        close_archives()
        logger.info("deinitializing globals...")
        logger.info("globals deinitialized!")
