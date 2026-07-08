"""
This module defines all custom exceptions for the banking system.
Each exception contains a default user-friendly error message and an HTTP status code.
"""

class BankException(Exception):
    """
    Base exception for all banking business logic errors.
    """
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class EntityNotFoundException(BankException):
    """
    Exception raised when a requested user or account does not exist.
    Generates an HTTP 404 (Not Found) error.
    """
    def __init__(self, message: str = "The requested resource (user or account) was not found."):
        super().__init__(message, status_code=404)

class FrozenAccountException(BankException):
    """
    Exception raised when a transaction is attempted on a frozen account.
    Generates an HTTP 400 (Bad Request) error.
    """
    def __init__(self, message: str = "This bank account is frozen. All operations are temporarily blocked."):
        super().__init__(message, status_code=400)

class InactiveUserException(BankException):
    """
    Exception raised when an operation involves a deactivated user.
    Generates an HTTP 400 (Bad Request) error.
    """
    def __init__(self, message: str = "The user associated with this account is deactivated. Operation aborted."):
        super().__init__(message, status_code=400)

class InsufficientFundsException(BankException):
    """
    Exception raised when an account balance is insufficient for a withdrawal or transfer.
    Generates an HTTP 400 (Bad Request) error.
    """
    def __init__(self, message: str = "Insufficient funds on the account to perform this operation."):
        super().__init__(message, status_code=400)

class LimitExceededException(BankException):
    """
    Exception raised when a daily transaction limit or maximum number of transfers is exceeded.
    Generates an HTTP 400 (Bad Request) error.
    """
    def __init__(self, message: str = "The authorized daily operations limit for this account has been exceeded."):
        super().__init__(message, status_code=400)