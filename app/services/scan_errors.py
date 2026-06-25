class ScanInputInvalid(Exception):
    pass


class ScanRecognitionFailed(Exception):
    def __init__(
        self,
        message: str,
        reason: str,
        label: str | None = None,
        confidence: float | None = None,
        minimum_confidence: float | None = None,
    ):
        super().__init__(message)
        self.reason = reason
        self.label = label
        self.confidence = confidence
        self.minimum_confidence = minimum_confidence


class ScanKnowledgeEnrichmentFailed(Exception):
    pass


class ScanCreationFailed(Exception):
    pass
