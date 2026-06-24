class CategoryAssignmentError(Exception):
    pass


class CategoryAssignmentUnavailable(CategoryAssignmentError):
    pass


class InvalidCategoryAssignmentResponse(CategoryAssignmentError):
    pass

