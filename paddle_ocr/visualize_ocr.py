import cv2
from ocr_engine import DocumentOCR


IMAGE_PATH = "test_images/1.png"
OUTPUT_PATH = "outputs/ocr_visualization.jpg"


# Create OCR engine
ocr = DocumentOCR()

# Run OCR
result = ocr.extract_text(IMAGE_PATH)

# Load original image
image = cv2.imread(IMAGE_PATH)

if image is None:
    raise FileNotFoundError(
        f"Could not load {IMAGE_PATH}"
    )


# Draw OCR detections
for detection in result:

    x1, y1, x2, y2 = map(
        int,
        detection["bbox"]
    )

    text = detection["text"]
    confidence = detection["confidence"]

    # Bounding box
    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        3
    )

    # Text + confidence
    label = f"{text} ({confidence:.2f})"

    cv2.putText(
        image,
        label,
        (x1, max(y1 - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


# Save visualization
cv2.imwrite(
    OUTPUT_PATH,
    image
)

print(
    f"OCR visualization saved to: {OUTPUT_PATH}"
)