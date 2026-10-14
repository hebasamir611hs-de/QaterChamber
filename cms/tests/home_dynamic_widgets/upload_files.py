"""Runtime-generated upload files for PBI 129384's Widget Image cases.

Generated into a temp dir at test time with QCTEST names, never committed to
`fixtures/` (that folder is owned by tools/fixture_factory.py). Sizes follow
the test cases' own wording (e.g. "marhaba_en_3mb.jpg (3MB)").
"""

from __future__ import annotations

import struct
import tempfile
import uuid
import zipfile
from pathlib import Path

FIXTURES = Path("web/tests/home_dynamic_widgets/fixtures")
MB = 1024 * 1024


def _dest(stem: str, suffix: str) -> Path:
    return Path(tempfile.gettempdir()) / f"QCTEST-{stem}-{uuid.uuid4().hex[:8]}{suffix}"


def padded_copy(src_name: str, stem: str, size_bytes: int) -> str:
    """A valid image (the fixture) padded with trailing bytes up to `size_bytes`.
    JPEG/PNG decoders ignore data after EOI/IEND, so the file stays a real image."""
    src = (FIXTURES / src_name).read_bytes()
    out = _dest(stem, Path(src_name).suffix)
    out.write_bytes(src + b"\0" * max(0, size_bytes - len(src)))
    return str(out)


def big_svg(stem: str, size_bytes: int) -> str:
    head = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/><!--'
    tail = b"--></svg>"
    out = _dest(stem, ".svg")
    out.write_bytes(head + b"Q" * max(0, size_bytes - len(head) - len(tail)) + tail)
    return str(out)


def pdf(stem: str) -> str:
    out = _dest(stem, ".pdf")
    out.write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )
    return str(out)


def docx(stem: str) -> str:
    out = _dest(stem, ".docx")
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", "<w:document/>")
    return str(out)


def bmp(stem: str) -> str:
    w = h = 2
    row = b"\xff\x00\x00" * w + b"\0" * ((4 - (w * 3) % 4) % 4)
    pixels = row * h
    header = b"BM" + struct.pack("<IHHI", 54 + len(pixels), 0, 0, 54)
    dib = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
    out = _dest(stem, ".bmp")
    out.write_bytes(header + dib + pixels)
    return str(out)


def tiff(stem: str) -> str:
    # 1x1 8-bit greyscale baseline TIFF
    entries = [(256, 3, 1, 1), (257, 3, 1, 1), (258, 3, 1, 8), (259, 3, 1, 1), (262, 3, 1, 1),
               (273, 4, 1, 8 + 2 + 12 * 8 + 4), (277, 3, 1, 1), (279, 4, 1, 1)]
    ifd = struct.pack("<H", len(entries)) + b"".join(
        struct.pack("<HHI", t, typ, n) + (struct.pack("<HH", v, 0) if typ == 3 else struct.pack("<I", v))
        for t, typ, n, v in entries) + struct.pack("<I", 0)
    out = _dest(stem, ".tif")
    out.write_bytes(b"II*\0" + struct.pack("<I", 8) + ifd + b"\x80")
    return str(out)


def valid(name: str) -> str:
    """Path of a committed valid fixture (marhaba_en.jpg, marhaba_ar.png, b2b_en.jpg, b2b_ar.svg)."""
    return str(FIXTURES / name)
