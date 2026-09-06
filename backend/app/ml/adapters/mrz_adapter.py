"""
TEAM MEMBER 3 (MRZ Parser — passport MRZ extraction and validation): implement here.

MRZ parsing/validation is deterministic (ICAO 9303 field layout + check-digit
arithmetic), not a trained model, so there's no `model_path` to configure — just
implement `parse()` directly.

1. Implement `parse()`: split the two (or three, for TD1) MRZ lines, extract each
   field by fixed character position, and compute/verify the check digits.
2. Point MRZ_ADAPTER_CLASS in .env at this class:
     MRZ_ADAPTER_CLASS=app.ml.adapters.mrz_adapter.MRZParserAdapter

Input contract: `mrz_text` is the raw MRZ text already isolated by the pipeline
(OCR output run on the region YOLO flagged as `mrz_zone`) — you receive plain text,
not an image.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.ml.interfaces import BaseMRZParser
from app.schemas.verification import MRZResult

logger = get_logger(__name__)


class MRZParserAdapter(BaseMRZParser):
    def __init__(self) -> None:
        logger.info("MRZParserAdapter initialized (not yet implemented)")

    def parse(self, mrz_text: str) -> MRZResult:
        # TODO(team-member-3): parse `mrz_text` per ICAO 9303 field positions and
        # compute check digits, e.g.:
        #     lines = mrz_text.strip().splitlines()
        #     document_number = lines[1][0:9]
        #     checksum_results = [MRZFieldCheck(field_name="document_number",
        #                                        checksum_valid=_verify_check_digit(...))]
        #     return MRZResult(raw_mrz_lines=lines, document_number=document_number,
        #                       checksum_results=checksum_results,
        #                       all_checksums_valid=all(c.checksum_valid for c in checksum_results))
        raise NotImplementedError(
            "MRZParserAdapter.parse() is a scaffold stub — implement real MRZ "
            "field extraction and checksum validation before this adapter is used "
            "in production."
        )
