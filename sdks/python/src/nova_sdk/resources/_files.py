"""Helpers for building multipart file parts."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import BinaryIO

from nova_sdk.exceptions import NovaValidationError

FileInput = bytes | str | os.PathLike[str] | BinaryIO


def build_file_part(
    file: FileInput,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> tuple[str, bytes, str]:
    """Normalize ``file`` into an ``(filename, content, content_type)`` multipart part.

    Accepts raw bytes, a filesystem path (``pathlib.Path`` or ``os.PathLike``),
    or a readable binary stream. Plain ``str`` values are treated as file *content*
    only when ``filename`` is supplied; otherwise they are treated as a path.
    Streams are read from their current position and are not rewound.
    """
    name = filename
    if isinstance(file, bytes):
        content = file
    elif isinstance(file, str) and filename is not None:
        content = file.encode("utf-8")
    elif isinstance(file, (str, os.PathLike)):
        path = Path(file)
        if not path.is_file():
            raise NovaValidationError(f"file path does not exist: {path}")
        content = path.read_bytes()
        name = name or path.name
    elif hasattr(file, "read"):
        data = file.read()
        content = data.encode("utf-8") if isinstance(data, str) else data
        name = name or Path(str(getattr(file, "name", ""))).name or None
    else:
        raise NovaValidationError(
            "file must be bytes, a path, or a readable binary stream."
        )

    if not content:
        raise NovaValidationError(
            "file content is empty. If passing an open stream, rewind it first "
            "(file.seek(0))."
        )
    if not name:
        raise NovaValidationError("filename is required when uploading raw bytes.")

    mime = content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    return name, content, mime
