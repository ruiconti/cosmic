from typing import List


class InvalidSku(Exception):
    def __init__(self, message: str, errors: List):
        super().__init__(message)
        self.errors = errors
