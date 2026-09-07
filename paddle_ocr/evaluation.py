import re


def normalize_text(text):
    """
    Normalize text before comparison.

    Removes spaces and converts everything to uppercase.
    """

    text = str(text).upper()

    text = re.sub(r"\s+", "", text)

    return text


def calculate_character_accuracy(expected, detected):
    """
    Calculate character-level similarity between
    expected and detected text.
    """

    expected = normalize_text(expected)
    detected = normalize_text(detected)

    if not expected:
        return 0.0

    # Dynamic programming edit distance
    previous = list(range(len(detected) + 1))

    for i, expected_char in enumerate(expected, start=1):

        current = [i]

        for j, detected_char in enumerate(
            detected,
            start=1
        ):

            insertion = current[j - 1] + 1
            deletion = previous[j] + 1

            substitution = previous[j - 1]

            if expected_char != detected_char:
                substitution += 1

            current.append(
                min(
                    insertion,
                    deletion,
                    substitution
                )
            )

        previous = current

    edit_distance = previous[-1]

    accuracy = (
        1 -
        edit_distance / max(
            len(expected),
            len(detected),
            1
        )
    )

    return max(0.0, accuracy)


def evaluate_detection(expected, detected):
    """
    Evaluate one expected text value against
    an OCR detection.
    """

    accuracy = calculate_character_accuracy(
        expected,
        detected
    )

    return {
        "expected": expected,
        "detected": detected,
        "accuracy": accuracy
    }