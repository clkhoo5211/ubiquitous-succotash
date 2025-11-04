"""Custom exceptions for the application"""

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception for all API exceptions"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


# User exceptions
class UserAlreadyExistsError(BaseAPIException):
    """Raised when attempting to create a user that already exists"""
    def __init__(self, detail: str = "User already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class UserNotFoundError(BaseAPIException):
    """Raised when user is not found"""
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class InvalidCredentialsError(BaseAPIException):
    """Raised when credentials are invalid"""
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


# Content exceptions
class PostNotFoundError(BaseAPIException):
    """Raised when post is not found"""
    def __init__(self, detail: str = "Post not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class CommentNotFoundError(BaseAPIException):
    """Raised when comment is not found"""
    def __init__(self, detail: str = "Comment not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ChannelNotFoundError(BaseAPIException):
    """Raised when channel is not found"""
    def __init__(self, detail: str = "Channel not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class TagNotFoundError(BaseAPIException):
    """Raised when tag is not found"""
    def __init__(self, detail: str = "Tag not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


# Permission exceptions
class PermissionDeniedError(BaseAPIException):
    """Raised when user doesn't have permission"""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotOwnerError(BaseAPIException):
    """Raised when user is not the owner of a resource"""
    def __init__(self, detail: str = "You are not the owner of this resource"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


# Validation exceptions
class ValidationError(BaseAPIException):
    """Raised when validation fails"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DuplicateLikeError(BaseAPIException):
    """Raised when attempting to like content twice"""
    def __init__(self, detail: str = "You have already liked this content"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class SelfLikeError(BaseAPIException):
    """Raised when attempting to like own content"""
    def __init__(self, detail: str = "You cannot like your own content"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


# Blockchain exceptions
class BlockchainError(BaseAPIException):
    """Raised when blockchain operation fails"""
    def __init__(self, detail: str = "Blockchain operation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsufficientBalanceError(BaseAPIException):
    """Raised when wallet has insufficient balance"""
    def __init__(self, detail: str = "Insufficient balance"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InsufficientPointsError(BaseAPIException):
    """Raised when user has insufficient points"""
    def __init__(self, detail: str = "Insufficient points"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidWalletAddressError(BaseAPIException):
    """Raised when wallet address is invalid"""
    def __init__(self, detail: str = "Invalid wallet address"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


# Storage exceptions
class StorageError(BaseAPIException):
    """Raised when storage operation fails"""
    def __init__(self, detail: str = "Storage operation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IPFSError(BaseAPIException):
    """Raised when IPFS operation fails"""
    def __init__(self, detail: str = "IPFS operation failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Moderation exceptions
class ContentModerationError(BaseAPIException):
    """Raised when content violates moderation rules"""
    def __init__(self, detail: str = "Content violates community guidelines"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UserBannedError(BaseAPIException):
    """Raised when user is banned"""
    def __init__(self, detail: str = "Your account has been banned"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class UserSuspendedError(BaseAPIException):
    """Raised when user is suspended"""
    def __init__(self, detail: str = "Your account has been suspended"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


# Rate limiting exceptions
class RateLimitExceededError(BaseAPIException):
    """Raised when rate limit is exceeded"""
    def __init__(self, detail: str = "Rate limit exceeded. Please try again later"):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


# OAuth exceptions
class OAuthError(BaseAPIException):
    """Raised when OAuth operation fails"""
    def __init__(self, detail: str = "OAuth authentication failed"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class OAuthProviderError(BaseAPIException):
    """Raised when OAuth provider returns an error"""
    def __init__(self, detail: str = "OAuth provider error"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)
