"""
Handles validation and temporary storage of uploaded document images.

Deliberately does NOT persist uploads long-term or write anything to the database —
per the architecture's data-retention rules, uploaded document images are processed
and then deleted; only structured results (not raw images) are ever meant to be
kept beyond the request lifecycle. This service only manages the short-lived
temp file needed to hand bytes to the ML adapters.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def read_and_validate(self, file: UploadFile) -> bytes:
        """
        Reads the full upload into memory and validates extension + size.
        Returns raw bytes — this is what gets passed to the ML adapters.
        """
        extension = self._extension_of(file.filename)
        if extension not in settings.allowed_upload_extensions_list:
            raise ValidationError(
                f"Unsupported file type '.{extension}'. Allowed types: "
                f"{', '.join(settings.allowed_upload_extensions_list)}."
            )

        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise ValidationError(
                f"File too large ({size_mb:.1f} MB). Maximum allowed is "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        if len(contents) == 0:
            raise ValidationError("Uploaded file is empty.")

        return contents

    def save_temp(self, contents: bytes, extension: str) -> Path:
        """
        Persists bytes to a short-lived temp file, in case an adapter needs a file
        path rather than raw bytes. Caller is responsible for calling cleanup().
        """
        temp_path = self.upload_dir / f"{uuid.uuid4()}.{extension}"
        temp_path.write_bytes(contents)
        return temp_path

    def cleanup(self, path: Path) -> None:
        try:
            if path.exists():
                os.remove(path)
        except OSError:
            logger.warning("Failed to clean up temp upload file: %s", path)

    @staticmethod
    def _extension_of(filename: str | None) -> str:
        if not filename or "." not in filename:
            return ""
        return filename.rsplit(".", 1)[-1].lower()
