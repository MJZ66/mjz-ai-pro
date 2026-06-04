import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.document_loader import DocumentLoadError, load_from_bytes
from utils.file_utils import load_from_bytes as util_load


def test_load_txt():
    text = load_from_bytes(b"hello world", "note.txt")
    assert text == "hello world"


def test_load_md_bytes():
    loaded = util_load(b"# Title\n\nbody", "readme.md")
    assert "Title" in loaded.text


def test_unsupported_zip():
    with pytest.raises(DocumentLoadError):
        load_from_bytes(b"x", "file.zip")


def test_image_rejected_in_rag_loader():
    from rag.document_loader import load_from_upload

    class Fake:
        name = "a.png"
        type = "image/png"

        def read(self):
            return b"\x89PNG\r\n\x1a\n"

    with pytest.raises(DocumentLoadError):
        load_from_upload(Fake())
