#!/usr/bin/env python
"""
tools/fixture_factory.py — generate the upload-test binary fixtures instead of
committing them.

WHY
---
As of 2026-09-30 the repo tracks 72 binary fixture files totalling ~110 MB,
including a 23 MB PNG and a 13 MB JPG, plus obvious duplication
(`valid_pdf_4mb.pdf` x4, `oversized_pdf_6mb.pdf` x3, `pdf_at_5mb_boundary.pdf`
x3). Their only meaningful properties are **byte size** and **format magic** —
they exist to exercise upload size limits and format rejection. That is a
function, not an asset.

DESIGN
------
- **Pure standard library at runtime.** Pillow is installed on some machines but
  is NOT in requirements.txt, so CI would not have it.
- **Byte-exact.** Each file is produced at exactly the size recorded in
  MANIFEST, because the tests assert boundary behaviour (e.g.
  `pdf_at_5mb_boundary.pdf` must be exactly 5 MiB).
- **Format-valid.** Padding is carried in a legal container slot — a PDF comment
  block, a PNG ancillary `tEXt` chunk, JPEG `COM` segments, a GIF Comment
  Extension — never appended as trailing garbage. Hand-rolling JPEG and GIF
  headers was tried first and produced files Pillow could not decode, so those
  two pad a known-good embedded 1x1 file instead.
- **Zero test changes.** Files are written to the SAME paths the tests already
  reference, so `FIXTURES = "..."` constants and every
  `upload_file(f"{FIXTURES}/valid_pdf_4mb.pdf")` keep working.

BEFORE UNTRACKING THE COMMITTED ORIGINALS
-----------------------------------------
These files satisfy the *size and format* contract, verified by decoding every
generated image with Pillow. Whether Liferay's uploader accepts a synthetic
JPEG/PNG/PDF as valid content has NOT been verified against qcdev. Run one real
upload test green against generated fixtures before deleting the originals.

USAGE
    python tools/fixture_factory.py            # create any missing fixtures
    python tools/fixture_factory.py --force    # rewrite all
    python tools/fixture_factory.py --verify   # report problems, write nothing
"""

from __future__ import annotations

import argparse
import base64
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# path -> (kind, exact size in bytes). Sizes captured from the committed
# originals on 2026-09-30.
MANIFEST: dict[str, tuple[str, int]] = {}


def _reg(paths: list[str], kind: str, size: int) -> None:
    for p in paths:
        MANIFEST[p] = (kind, size)


# --- PDFs -------------------------------------------------------------------
_reg([f"cms/tests/{m}/fixtures/oversized_pdf_6mb.pdf"
      for m in ("publications", "export_reports", "annual_reports")], "pdf", 6291456)
_reg([f"cms/tests/{m}/fixtures/pdf_at_5mb_boundary.pdf"
      for m in ("publications", "export_reports", "annual_reports")], "pdf", 5242880)
_reg([f"cms/tests/{m}/fixtures/valid_pdf_4mb.pdf"
      for m in ("publications", "export_reports", "annual_reports",
                "al_moltaqa_magazine")], "pdf", 4194304)
_reg(["cms/tests/home_publications/fixtures/publication_attachment_qctest.pdf"],
     "pdf", 4000038)

# --- PNGs -------------------------------------------------------------------
_reg(["web/tests/home_about_summary/fixtures/about_counter_icon_oversized.png"],
     "png", 23530664)
_reg([f"cms/tests/{m}/fixtures/oversized_cover_2_5mb.png"
      for m in ("export_reports", "annual_reports")], "png", 2621440)
_reg(["cms/tests/home_social_icons/fixtures/icon_2_5mb.png"], "png", 2621440)
_reg(["cms/tests/home_social_icons/fixtures/icon_1_5mb.png"], "png", 1572864)
_reg(["web/tests/home_strategic_partners/fixtures/partner_logo_qctest.png"], "png", 51200)
_reg(["cms/tests/home_social_icons/fixtures/icon_500kb.png"], "png", 512000)
_reg(["web/tests/home_dynamic_widgets/fixtures/marhaba_ar.png"], "png", 390)

# --- JPEGs ------------------------------------------------------------------
_reg(["web/tests/home_about_summary/fixtures/about_building_oversized.jpg"],
     "jpg", 13207467)
_reg(["web/tests/org_structure/fixtures/photo_large_2_8mb.jpg"], "jpg", 2936358)
_reg(["cms/tests/org_structure/fixtures/photo_large_2_8mb.jpg"], "jpg", 2936012)
_reg(["web/tests/org_structure/fixtures/photo_exact_2mb.jpg",
      "cms/tests/org_structure/fixtures/photo_exact_2mb.jpg"], "jpg", 2097152)
_reg([f"cms/tests/{m}/fixtures/valid_cover_1_5mb.jpg"
      for m in ("publications", "export_reports", "annual_reports",
                "al_moltaqa_magazine")], "jpg", 1639132)
_reg(["cms/tests/export_reports/fixtures/report-cover-q4-2024.jpg"], "jpg", 1639132)
_reg(["cms/tests/home_publications/fixtures/publication_cover_image_qctest.jpg"],
     "jpg", 1000064)
_reg(["cms/tests/org_structure/fixtures/photo.jpg"], "jpg", 1304)
_reg(["web/tests/home_dynamic_widgets/fixtures/marhaba_en.jpg",
      "web/tests/home_dynamic_widgets/fixtures/b2b_en.jpg"], "jpg", 1045)
_reg(["web/tests/home_about_summary/fixtures/about_building_primary.jpg",
      "web/tests/home_about_summary/fixtures/about_building_secondary.jpg"], "jpg", 789)
_reg(["web/tests/org_structure/fixtures/photo.jpg",
      "web/tests/org_structure/fixtures/banner_en.jpg"], "jpg", 346)

# --- Deliberately-unsupported formats (must be REJECTED by the uploader) -----
_reg([f"cms/tests/{m}/fixtures/unsupported_cover.bmp"
      for m in ("export_reports", "annual_reports")], "bmp", 30054)
_reg(["cms/tests/org_structure/fixtures/photo.bmp"], "bmp", 30054)
_reg(["web/tests/home_about_summary/fixtures/about_counter_icon_invalid.bmp"],
     "bmp", 3126)
_reg([f"cms/tests/{m}/fixtures/unsupported_cover.gif"
      for m in ("publications", "export_reports", "annual_reports",
                "al_moltaqa_magazine")], "gif", 365)
_reg([f"cms/tests/{m}/fixtures/unsupported_report.docx"
      for m in ("export_reports", "annual_reports")], "docx", 2004)
_reg(["cms/tests/al_moltaqa_magazine/fixtures/issue211.docx"], "docx", 2254)
_reg([f"cms/tests/{m}/fixtures/report.exe"
      for m in ("publications", "export_reports")], "exe", 2004)
_reg(["cms/tests/home_social_icons/fixtures/icon_200kb.svg"], "svg", 204800)

# --- Site Header logo (PBI 129363, eng-header, 2026-10-01) -------------------
# Named QCTEST-<tc_id>-logo.* so every copy uploaded into Documents & Media is
# recognisable as disposable test data (D&M deletion is not approved).
_reg(["cms/tests/components/fixtures/QCTEST-134270-logo.png"], "png", 512000)
_reg(["cms/tests/components/fixtures/QCTEST-134272-logo.jpg"], "jpg", 3145728)


# --- Phase 3 CMS batch 2026-10-01 (PBIs 130708/130713/130714/130715/131061/131062)
# One set per module so each test module only reads its own fixtures/ folder.
_P3_MODULES = ("made_in_qatar_expo", "podcast", "photo_albums", "video_library",
               "media_dept_request", "advertisements")
for _m in _P3_MODULES:
    _d = f"cms/tests/{_m}/fixtures"
    _reg([f"{_d}/valid_image_500kb.jpg"], "jpg", 512000)
    _reg([f"{_d}/valid_icon_200kb.png"], "png", 204800)
    _reg([f"{_d}/valid_icon_45kb.svg"], "svg", 46080)
    _reg([f"{_d}/oversized_image_3mb.jpg"], "jpg", 3145728)
    _reg([f"{_d}/oversized_icon_1_5mb.png"], "png", 1572864)
    _reg([f"{_d}/unsupported_image.bmp"], "bmp", 30054)
    _reg([f"{_d}/unsupported_image.gif"], "gif", 365)
    _reg([f"{_d}/unsupported_image.pdf"], "pdf", 20480)
    _reg([f"{_d}/unsupported_file.docx"], "docx", 2004)
    _reg([f"{_d}/unsupported_file.exe"], "exe", 2004)
# --- Phase 3 CMS batch 2026-10-01b, Engineer B (PBIs 130720/130947/130949) --
# Same image/file set as _P3_MODULES plus the PDFs these modules upload.
# Shared-tool change approved by the user 2026-10-01.
for _m in ("partners_offers", "certificate_of_origin", "proposal_for_research"):
    _d = f"cms/tests/{_m}/fixtures"
    _reg([f"{_d}/valid_image_500kb.jpg"], "jpg", 512000)
    _reg([f"{_d}/valid_icon_200kb.png"], "png", 204800)
    _reg([f"{_d}/oversized_image_3mb.jpg"], "jpg", 3145728)
    _reg([f"{_d}/unsupported_image.bmp"], "bmp", 30054)
    _reg([f"{_d}/unsupported_file.exe"], "exe", 2004)
    _reg([f"{_d}/valid_form.docx"], "docx", 2004)
    _reg([f"{_d}/valid_pdf_4mb.pdf"], "pdf", 4194304)
    _reg([f"{_d}/valid_pdf_3mb.pdf"], "pdf", 3355443)
    _reg([f"{_d}/oversized_pdf_6mb.pdf"], "pdf", 6291456)
_reg(["cms/tests/media_dept_request/fixtures/valid_press_kit_3mb.pdf"], "pdf", 3355443)
_reg(["cms/tests/media_dept_request/fixtures/oversized_press_kit_6mb.pdf"], "pdf", 5872025)
_reg(["cms/tests/podcast/fixtures/valid_episode_audio.mp3"], "mp3", 262144)
_reg(["cms/tests/podcast/fixtures/unsupported_episode_audio.wma"], "wma", 65536)
_reg(["cms/tests/video_library/fixtures/valid_video_1mb.mp4"], "mp4", 1048576)
_reg(["cms/tests/video_library/fixtures/unsupported_video.avi"], "avi", 65536)


# A real 1x1 grayscale JPEG (159 bytes — the smallest Pillow will emit that
# still decodes) and a real 1x1 GIF87a (37 bytes), produced once with Pillow at
# authoring time and embedded so runtime generation stays pure-stdlib.
# The JPEG must stay SMALL: the manifest's smallest jpg fixture is 346 bytes,
# and a baseline larger than that could only be produced truncated.
_JPEG_1PX = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////"
    "////////////////////////////////////////////////wAALCAABAAEBAREA/8QAFAAB"
    "AAAAAAAAAAAAAAAAAAAAA//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AN//Z"
)
_GIF_1PX = base64.b64decode("R0lGODdhAQABAIAAAAAAAAAAACwAAAAAAQABAAAIBAABBAQAOw==")

NUL = b"\x00"


def _partition(need: int, overhead: int = 1, max_payload: int = 255) -> list[int]:
    """Split `need` bytes into payload sizes, each costing `overhead` extra.

    Every chunk consumes `overhead + n` bytes of the region, with
    1 <= n <= max_payload. Returns the n values, guaranteed to total exactly
    `need` — a plain greedy split can strand a remainder too small to form a
    legal chunk, so the last full chunk is shrunk to absorb it.
    """
    if need <= 0:
        return []
    step = max_payload + overhead
    out: list[int] = []
    while need > step:
        out.append(max_payload)
        need -= step
    if need < overhead + 1:
        if not out:
            raise ValueError(f"cannot pad {need} bytes with overhead {overhead}")
        borrow = (overhead + 1) - need
        out[-1] -= borrow
        need += borrow
    out.append(need - overhead)
    return out


def make_pdf(size: int) -> bytes:
    """A parseable single-page PDF padded to `size` via a comment block.

    Padding sits between the header and the body as a `%`-prefixed comment,
    which the spec tells parsers to ignore — so the file stays valid at any size
    rather than being a header with garbage stapled on.
    """
    head = b"%PDF-1.4\n"
    body = (
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n0\n%%EOF\n"
    )
    overhead = len(head) + len(body)
    if size <= overhead:
        return (head + body)[:size].ljust(size, b"\n")
    pad = size - overhead
    chunk = b"%" + b"Q" * (pad - 2) + b"\n" if pad >= 2 else b"\n" * pad
    return head + chunk + body


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def make_png(size: int) -> bytes:
    """A valid 1x1 PNG padded to `size` with an ancillary `tEXt` chunk.

    `tEXt` is ancillary and safe-to-copy, so conformant decoders skip it and the
    image stays decodable at any size.
    """
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = _png_chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = _png_chunk(b"IEND", b"")
    base = len(sig) + len(ihdr) + len(idat) + len(iend)
    if size <= base:
        return (sig + ihdr + idat + iend)[:size].ljust(size, NUL)
    need = size - base - 12          # 12 = tEXt chunk length+tag+CRC overhead
    keyword = b"Comment\x00"
    payload = keyword + b"P" * max(0, need - len(keyword))
    return sig + ihdr + _png_chunk(b"tEXt", payload) + idat + iend


def make_jpg(size: int) -> bytes:
    """A real decodable JPEG padded to `size` with COM (comment) segments.

    COM segments are inserted directly after SOI — a legal position that
    decoders skip — so the result is a genuine JPEG at any size. Each segment
    costs 4 bytes of overhead and caps its payload at 65533.
    """
    base = _JPEG_1PX
    if size <= len(base):
        # Too small to hold a real JPEG. These tiny fixtures exist only to be
        # rejected on format/size, never decoded.
        return base[:size].ljust(size, NUL)
    coms = bytearray()
    for payload in _partition(size - len(base), overhead=4, max_payload=65533):
        coms += b"\xff\xfe" + struct.pack(">H", payload + 2) + b"J" * payload
    return base[:2] + bytes(coms) + base[2:]


def make_gif(size: int) -> bytes:
    """A real GIF87a padded to `size` with a Comment Extension before the
    trailer — a legal top-level block that decoders skip."""
    base = _GIF_1PX
    if size <= len(base):
        return base[:size].ljust(size, NUL)
    body, trailer = base[:-1], base[-1:]
    need = size - len(base) - 3      # 3 = 0x21 0xFE ... 0x00
    blocks = bytearray(b"\x21\xfe")
    for n in _partition(need, overhead=1, max_payload=255):
        blocks += bytes([n]) + b"G" * n
    blocks += NUL
    return body + bytes(blocks) + trailer


def make_bmp(size: int) -> bytes:
    """A BMP whose header declares exactly `size` bytes."""
    px = max(0, size - 54)
    hdr = (b"BM" + struct.pack("<IHHI", size, 0, 0, 54)
           + struct.pack("<IiiHHIIiiII", 40, 1, 1, 1, 24, 0, px, 2835, 2835, 0, 0))
    return (hdr + NUL * px)[:size].ljust(size, NUL)


def make_docx(size: int) -> bytes:
    """PK-magic file. These fixtures exist to be REJECTED, so magic + size is
    the whole contract — never opened as a real document."""
    return (b"PK\x03\x04" + NUL * 26 + b"D" * max(0, size - 30))[:size].ljust(size, NUL)


def make_exe(size: int) -> bytes:
    """MZ-magic file — same rationale as docx: must be rejected, not run."""
    return (b"MZ\x90\x00" + b"E" * max(0, size - 4))[:size].ljust(size, NUL)


def make_svg(size: int) -> bytes:
    head = b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
    tail = b"</svg>"
    pad = max(0, size - len(head) - len(tail) - 7)
    return (head + b"<!--" + b"S" * pad + b"-->" + tail)[:size].ljust(size, b" ")


def make_mp3(size: int) -> bytes:
    """ID3v2 tag + repeated MPEG-1 Layer III frame headers (128 kbps,
    44.1 kHz, 417-byte frames) — enough for a magic/extension check."""
    id3 = b"ID3" + bytes([3, 0, 0, 0, 0, 0, 0])
    frame = bytes([0xFF, 0xFB, 0x90, 0x64]) + NUL * 413
    body = id3 + frame * (size // len(frame) + 1)
    return body[:size]


def make_mp4(size: int) -> bytes:
    """ISO-BMFF `ftyp` box (isom) followed by one `mdat` box filling the size."""
    import struct

    ftyp = struct.pack(">I", 24) + b"ftypisom" + struct.pack(">I", 0x200) + b"isommp41"
    mdat_len = size - len(ftyp)
    return ftyp + struct.pack(">I", mdat_len) + b"mdat" + NUL * (mdat_len - 8)


def make_wma(size: int) -> bytes:
    """ASF header-object GUID — must be REJECTED as an unsupported audio type."""
    guid = bytes.fromhex("3026B2758E66CF11A6D900AA0062CE6C")
    return (guid + NUL * size)[:size]


def make_avi(size: int) -> bytes:
    """RIFF/AVI magic — must be REJECTED as an unsupported video type."""
    import struct

    return (b"RIFF" + struct.pack("<I", size - 8) + b"AVI LIST" + NUL * size)[:size]


BUILDERS = {
    "pdf": make_pdf, "png": make_png, "jpg": make_jpg, "gif": make_gif,
    "bmp": make_bmp, "docx": make_docx, "exe": make_exe, "svg": make_svg,
    "mp3": make_mp3, "mp4": make_mp4, "wma": make_wma, "avi": make_avi,
}


def ensure_fixtures(force: bool = False, root: Path | None = None) -> int:
    """Create any missing / wrong-sized fixture. Returns how many were written."""
    base = root or ROOT
    written = 0
    for rel, (kind, size) in MANIFEST.items():
        path = base / rel
        if not force and path.exists() and path.stat().st_size == size:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        data = BUILDERS[kind](size)
        if len(data) != size:
            raise AssertionError(
                f"{rel}: builder produced {len(data)} bytes, expected {size}")
        path.write_bytes(data)
        written += 1
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.verify:
        bad = []
        for rel, (_kind, size) in MANIFEST.items():
            p = ROOT / rel
            if not p.exists():
                bad.append(f"MISSING  {rel}")
            elif p.stat().st_size != size:
                bad.append(f"SIZE     {rel}: {p.stat().st_size} != {size}")
        print(f"{len(MANIFEST)} fixtures in manifest; {len(bad)} problem(s)")
        for b in bad[:40]:
            print("  " + b)
        return 1 if bad else 0

    n = ensure_fixtures(force=args.force)
    total = sum(s for _k, s in MANIFEST.values())
    print(f"{len(MANIFEST)} fixtures in manifest ({total / 1024 / 1024:.1f} MB total)")
    print(f"written this run: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
