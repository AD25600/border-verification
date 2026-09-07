import cv2


class DocumentPreprocessor:
    """
    Conservative preprocessing for document images.

    Currently:
    - Validates the image
    - Resizes very large images
    - Maintains the original aspect ratio

    More advanced preprocessing can be added later
    if evaluation shows that it improves OCR.
    """

    def __init__(self, max_side=4000):
        self.max_side = max_side

    def load_image(self, image_path):
        """
        Load an image from disk.
        """

        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(
                f"Could not load image: {image_path}"
            )

        return image

    def resize(self, image):
        """
        Resize an image only when its largest dimension
        exceeds the configured maximum.
        """

        height, width = image.shape[:2]

        largest_side = max(height, width)

        if largest_side <= self.max_side:
            return image

        scale = self.max_side / largest_side

        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

        return resized

    def preprocess(self, image_path):
        """
        Run the conservative preprocessing pipeline.
        """

        image = self.load_image(image_path)

        image = self.resize(image)

        return image