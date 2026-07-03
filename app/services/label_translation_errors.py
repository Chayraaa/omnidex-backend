class LabelTranslationError(Exception):
    pass


class LabelTranslationUnavailable(LabelTranslationError):
    pass


class InvalidLabelTranslationResponse(LabelTranslationError):
    pass
