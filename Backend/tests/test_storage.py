from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.storage import DiskObjectStorage


class DiskObjectStorageTestCase(unittest.TestCase):
    def test_put_get_delete_photo_and_account_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            storage = DiskObjectStorage(Path(tempdir) / "objects")

            storage.put_photo("account_1", "photo_1", b"photo-bytes", "image/jpeg")
            self.assertEqual(storage.get_photo("account_1", "photo_1"), b"photo-bytes")

            storage.delete_photo("account_1", "photo_1")
            self.assertIsNone(storage.get_photo("account_1", "photo_1"))

            storage.put_photo("account_1", "photo_2", b"second-photo", "image/jpeg")
            storage.delete_account("account_1")
            self.assertIsNone(storage.get_photo("account_1", "photo_2"))


if __name__ == "__main__":
    unittest.main()
