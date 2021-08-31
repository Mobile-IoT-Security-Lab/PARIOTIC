class UnsupportedBodyException(Exception):
    """
    A custom exception that is raised when the body of a QualifiedCondition contains unsupported instruction.
    In the first PoC we do not handled break, continue or return stmt. (See extract_body from QualifiedCondition class)
    """

    def __init__(self, message="The QC contains a break, continue or return stmt"):
        self.message = message
        super().__init__(self.message)


class UnsupportedConstantException(Exception):
    """
    A custom exception that is raised when the constant of a QualifiedCondition is not valid.
    """

    def __init__(self, message="The QC has a dummy constant value"):
        self.message = message
        super().__init__(self.message)