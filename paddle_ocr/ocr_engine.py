from pathlib import Path
from paddleocr import PaddleOCR


class DocumentOCR:
    """
    Reusable OCR module for document images.

    Output:
        A list of OCR detections containing:
        - text
        - confidence
        - bounding box
    """

    def __init__(self):
        self.ocr = PaddleOCR(
            lang="en",
            device="cpu",
            enable_mkldnn=False
        )

    def extract_text(self, image_path):
        """
        Run OCR on a document image.

        Args:
            image_path: Path to the document image.

        Returns:
            List of dictionaries containing OCR results.
        """

        image_path = Path(image_path)

        # Validate image path
        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        # Run PaddleOCR
        results = self.ocr.predict(str(image_path))

        detections = []

        # Process PaddleOCR results
        for result in results:

            texts = result["rec_texts"]
            scores = result["rec_scores"]
            boxes = result["rec_boxes"]

            for text, score, box in zip(
                texts,
                scores,
                boxes
            ):

                text = str(text).strip()

                # Ignore empty detections
                if not text:
                    continue

                detections.append({
                    "text": text,
                    "confidence": float(score),
                    "bbox": box.tolist()
                })

        return detections