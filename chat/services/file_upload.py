import os
import re
import unicodedata
from fastapi import HTTPException

# Mapping of allowed MIME types → their canonical safe extensions
_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}

# Magic-byte signatures for MIME detection (first N bytes → MIME type)
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),     # RIFF....WEBP — checked further below
    (b"%PDF", "application/pdf"),
    (b"PK\x03\x04", None),       # ZIP-based — could be docx, xlsx; resolved via extension below
    (b"\xd0\xcf\x11\xe0", "application/msword"),   # Compound Document (legacy .doc)
    (b"ID3", "audio/mpeg"),
    (b"\xff\xfb", "audio/mpeg"),
    (b"\xff\xf3", "audio/mpeg"),
    (b"\xff\xf2", "audio/mpeg"),
    (b"OggS", "audio/ogg"),
    (b"RIFF", "audio/wav"),      # RIFF....WAVE — checked further below
    (b"\x00\x00\x00", "video/mp4"),   # ftyp boxes — checked further below
    (b"ftyp", "video/mp4"),
]

def detect_mime(header: bytes, filename: str) -> str | None:
    """
    Detect MIME type from raw file header bytes and filename extension.
    Returns the MIME string or None if unknown / not detected.
    Priority: magic bytes > filename extension fallback for ZIP-based formats.
    """
    # WEBP: RIFF????WEBP
    if header[:4] == b"RIFF" and len(header) >= 12 and header[8:12] == b"WEBP":
        return "image/webp"

    # WAV: RIFF????WAVE
    if header[:4] == b"RIFF" and len(header) >= 12 and header[8:12] == b"WAVE":
        return "audio/wav"

    # MP4 ftyp box: bytes 4-7 == b"ftyp"
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "video/mp4"

    # MOV: ftyp box with qt   marker
    if len(header) >= 12 and header[4:8] == b"ftyp" and header[8:12] == b"qt  ":
        return "video/quicktime"

    # ZIP-based formats: docx or xlsx — resolve via extension
    if header[:4] == b"PK\x03\x04":
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if ext == "xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return None  # Unknown ZIP — reject

    # Other magic byte checks
    for signature, mime in _MAGIC_SIGNATURES:
        if header[:len(signature)] == signature and mime:
            return mime

    return None

def validate_file(
    file_bytes: bytes,
    filename: str,
    allowed_mimes: list[str],
    max_size: int,
    video_mimes: list[str],
    video_max_size: int,
) -> tuple[str, str]:
    """
    Validates a single file's size and MIME type.
    Returns (detected_mime, safe_extension) on success.
    Raises HTTPException on any validation failure.
    """
    size = len(file_bytes)

    if size == 0:
        raise HTTPException(status_code=400, detail=f"File '{filename}' is empty.")

    # Detect MIME from magic bytes
    detected_mime = detect_mime(file_bytes[:32], filename)
    if detected_mime is None:
        raise HTTPException(
            status_code=400,
            detail=f"File '{filename}' has an unrecognised or unsupported file type.",
        )

    if detected_mime not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"File '{filename}' has a disallowed file type ({detected_mime}).",
        )

    # Apply size limit (video gets a larger quota)
    effective_max = video_max_size if detected_mime in video_mimes else max_size
    if size > effective_max:
        limit_mb = effective_max // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File '{filename}' exceeds the {limit_mb} MB size limit.",
        )

    safe_ext = _MIME_TO_EXT.get(detected_mime, "bin")
    return detected_mime, safe_ext

def sanitize_filename(name: str) -> str:
    """Strip path components, whitespace and dangerous characters from a filename."""
    # Take only the basename
    name = os.path.basename(name)
    # Normalize unicode
    name = unicodedata.normalize("NFKD", name)
    # Keep only safe characters
    name = re.sub(r"[^\w\s\-\.]", "", name).strip()
    # Collapse multiple whitespace/dots
    name = re.sub(r"\s+", "_", name)
    return name or "file"
