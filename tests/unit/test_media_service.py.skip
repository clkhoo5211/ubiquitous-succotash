"""Unit tests for media_service

Tests IPFS upload, image optimization, and file management with mocked HTTP calls.
"""

import io
from typing import BinaryIO, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from PIL import Image

from src.core.exceptions import IPFSError, ValidationError
from src.schemas.media import ImageOptimizationRequest, MediaUploadResponse
from src.services.media_service import MediaService


class MockUploadFile(UploadFile):
    """Custom UploadFile mock that allows content_type setting"""

    def __init__(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ):
        super().__init__(file=file, filename=filename)
        self._content_type = content_type

    @property
    def content_type(self) -> Optional[str]:
        return self._content_type


@pytest.fixture
def media_service():
    """Create media service instance"""
    service = MediaService()
    service.api_key = "test_api_key"
    return service


@pytest.fixture
def mock_image_file():
    """Create mock image upload file"""
    # Create a small test image
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    upload_file = MockUploadFile(
        file=img_bytes,
        filename="test_image.jpg",
        content_type="image/jpeg",
    )
    return upload_file


@pytest.fixture
def mock_large_image_file():
    """Create mock large image that needs resizing"""
    # Create a large test image (3000x2000)
    img = Image.new("RGB", (3000, 2000), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    upload_file = MockUploadFile(
        file=img_bytes,
        filename="large_image.jpg",
        content_type="image/jpeg",
    )
    return upload_file


@pytest.fixture
def mock_video_file():
    """Create mock video upload file"""
    video_bytes = io.BytesIO(b"mock video data")

    upload_file = MockUploadFile(
        file=video_bytes,
        filename="test_video.mp4",
        content_type="video/mp4",
    )
    return upload_file


class TestFileValidation:
    """Test file validation logic"""

    def test_validate_supported_image(self, media_service, mock_image_file):
        """Test validation of supported image type"""
        is_valid, message = media_service.validate_file(mock_image_file)

        assert is_valid is True
        assert message == "Valid file"

    def test_validate_supported_video(self, media_service, mock_video_file):
        """Test validation of supported video type"""
        is_valid, message = media_service.validate_file(mock_video_file)

        assert is_valid is True
        assert message == "Valid file"

    def test_validate_unsupported_type(self, media_service):
        """Test validation of unsupported file type"""
        unsupported_file = MockUploadFile(
            file=io.BytesIO(b"pdf content"),
            filename="document.pdf",
            content_type="application/pdf",
        )

        is_valid, message = media_service.validate_file(unsupported_file)

        assert is_valid is False
        assert "Unsupported file type" in message


class TestImageOptimization:
    """Test image optimization functionality"""

    @pytest.mark.asyncio
    async def test_optimize_image_resize(self, media_service):
        """Test image resizing when larger than max dimensions"""
        # Create large image
        img = Image.new("RGB", (3000, 2000), color="green")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=95)
        original_content = img_bytes.getvalue()

        optimization_params = ImageOptimizationRequest(
            max_width=1920, max_height=1080, quality=85, format="JPEG"
        )

        optimized_content = await media_service.optimize_image(
            original_content, optimization_params
        )

        # Verify optimized image
        optimized_img = Image.open(io.BytesIO(optimized_content))
        assert optimized_img.width <= 1920
        assert optimized_img.height <= 1080
        # Optimized should be smaller
        assert len(optimized_content) < len(original_content)

    @pytest.mark.asyncio
    async def test_optimize_image_quality_reduction(self, media_service):
        """Test JPEG quality reduction"""
        # Create image
        img = Image.new("RGB", (800, 600), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=100)
        original_content = img_bytes.getvalue()

        optimization_params = ImageOptimizationRequest(
            max_width=1920, max_height=1080, quality=60, format="JPEG"
        )

        optimized_content = await media_service.optimize_image(
            original_content, optimization_params
        )

        # Lower quality should result in smaller file
        assert len(optimized_content) < len(original_content)

    @pytest.mark.asyncio
    async def test_optimize_image_rgba_to_rgb(self, media_service):
        """Test RGBA to RGB conversion for JPEG"""
        # Create RGBA image (with transparency)
        img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        original_content = img_bytes.getvalue()

        optimization_params = ImageOptimizationRequest(
            max_width=1920, max_height=1080, quality=85, format="JPEG"
        )

        optimized_content = await media_service.optimize_image(
            original_content, optimization_params
        )

        # Verify image is now RGB
        optimized_img = Image.open(io.BytesIO(optimized_content))
        assert optimized_img.mode == "RGB"

    @pytest.mark.asyncio
    async def test_optimize_image_error_returns_original(self, media_service):
        """Test that optimization errors return original content"""
        invalid_content = b"not an image"

        result = await media_service.optimize_image(invalid_content, ImageOptimizationRequest())

        # Should return original on error
        assert result == invalid_content


class TestIPFSUpload:
    """Test IPFS file upload"""

    @pytest.mark.asyncio
    async def test_upload_to_ipfs_success(self, media_service, mock_image_file):
        """Test successful IPFS upload"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Hash": "QmTest123456"}

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await media_service.upload_to_ipfs(mock_image_file, optimize_images=False)

            assert isinstance(result, MediaUploadResponse)
            assert result.success is True
            assert result.ipfs_hash == "QmTest123456"
            assert str(result.ipfs_url) == f"{media_service.gateway_url}QmTest123456"
            assert result.file_name == "test_image.jpg"
            assert result.mime_type == "image/jpeg"

    @pytest.mark.asyncio
    async def test_upload_to_ipfs_with_optimization(self, media_service, mock_large_image_file):
        """Test IPFS upload with image optimization enabled"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Hash": "QmTest789"}

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Read original size
            original_content = await mock_large_image_file.read()
            await mock_large_image_file.seek(0)

            result = await media_service.upload_to_ipfs(mock_large_image_file, optimize_images=True)

            assert result.success is True
            assert result.ipfs_hash == "QmTest789"
            # Optimized file should be smaller
            assert result.file_size < len(original_content)

    @pytest.mark.asyncio
    async def test_upload_to_ipfs_validation_error(self, media_service):
        """Test upload with invalid file type"""
        invalid_file = MockUploadFile(
            file=io.BytesIO(b"pdf content"),
            filename="document.pdf",
            content_type="application/pdf",
        )

        with pytest.raises(ValidationError) as exc_info:
            await media_service.upload_to_ipfs(invalid_file)

        assert "Unsupported file type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_to_ipfs_file_too_large(self, media_service):
        """Test upload with file exceeding size limit"""
        # Create file larger than max size
        large_content = b"x" * (media_service.max_file_size + 1)
        large_file = MockUploadFile(
            file=io.BytesIO(large_content),
            filename="huge.jpg",
            content_type="image/jpeg",
        )

        with pytest.raises(ValidationError) as exc_info:
            await media_service.upload_to_ipfs(large_file)

        assert "exceeds maximum" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_to_ipfs_lighthouse_error(self, media_service, mock_image_file):
        """Test upload when Lighthouse API returns error"""
        # Response should be regular MagicMock, not AsyncMock (it's already awaited)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            # post() returns mock_response after being awaited
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client_instance
            # __aexit__ should return None to propagate exceptions (not suppress them)
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(IPFSError) as exc_info:
                await media_service.upload_to_ipfs(mock_image_file)

            assert "IPFS upload failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_to_ipfs_no_hash_in_response(self, media_service, mock_image_file):
        """Test upload when Lighthouse doesn't return hash"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No Hash field

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client_instance
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client_class.return_value = mock_client

            with pytest.raises(IPFSError) as exc_info:
                await media_service.upload_to_ipfs(mock_image_file)

            assert "No IPFS hash returned" in str(exc_info.value)


class TestIPFSUnpin:
    """Test IPFS unpinning"""

    @pytest.mark.asyncio
    async def test_unpin_from_ipfs_success(self, media_service):
        """Test successful unpinning"""
        ipfs_hash = "QmTest123456"
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.delete.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await media_service.unpin_from_ipfs(ipfs_hash)

            assert result is True

    @pytest.mark.asyncio
    async def test_unpin_from_ipfs_failure(self, media_service):
        """Test unpinning failure"""
        ipfs_hash = "QmTest123456"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client.delete.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await media_service.unpin_from_ipfs(ipfs_hash)

            assert result is False

    @pytest.mark.asyncio
    async def test_unpin_from_ipfs_exception(self, media_service):
        """Test unpinning with exception"""
        ipfs_hash = "QmTest123456"

        with patch("src.services.media_service.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.delete = AsyncMock(side_effect=Exception("Network error"))

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client_instance
            mock_client.__aexit__.return_value = None  # Don't suppress exceptions
            mock_client_class.return_value = mock_client

            result = await media_service.unpin_from_ipfs(ipfs_hash)

            assert result is False


class TestMimeType:
    """Test MIME type detection"""

    def test_get_mime_type_image(self, media_service):
        """Test MIME type detection for images"""
        assert media_service.get_mime_type("photo.jpg") == "image/jpeg"
        assert media_service.get_mime_type("image.png") == "image/png"
        assert media_service.get_mime_type("animated.gif") == "image/gif"

    def test_get_mime_type_video(self, media_service):
        """Test MIME type detection for videos"""
        assert media_service.get_mime_type("video.mp4") == "video/mp4"
        assert media_service.get_mime_type("clip.webm") == "video/webm"

    def test_get_mime_type_unknown(self, media_service):
        """Test MIME type for unknown extension"""
        result = media_service.get_mime_type("file.unknown")
        assert result == "application/octet-stream"
