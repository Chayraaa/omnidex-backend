class RecognitionUnavailable(Exception):
    pass


class LowConfidence(Exception):
    def __init__(self, label: str, confidence: float, minimum_confidence: float):
        super().__init__(
            f"Recognition confidence for '{label}' was {confidence:.3f}, "
            f"below minimum {minimum_confidence:.3f}"
        )
        self.label = label
        self.confidence = confidence
        self.minimum_confidence = minimum_confidence


class InvalidRecognitionResponse(Exception):
    pass
