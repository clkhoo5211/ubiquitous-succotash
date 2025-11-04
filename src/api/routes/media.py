"""Media API routes (IPFS upload via Lighthouse)

Handles:
- File uploads to IPFS
- Image optimization
- Media management
- File unpinning
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.dependencies.auth import get_current_user as get_current_active_user
from src.core.exceptions import IPFSError, StorageError, ValidationError
from src.models.user import User
from src.schemas.media import MediaDeleteRequest, MediaDeleteResponse, MediaUploadResponse
from src.services.media_service import media_service

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(..., description="Media file to upload"),
    optimize: bool = True,
    current_user: User = Depends(get_current_active_user),
):
    """Upload media file to IPFS via Lighthouse

    **Supported File Types:**
    - Images: JPEG, PNG, GIF, WebP, SVG, HEIC
    - Videos: MP4, WebM, OGG, QuickTime (embedded links recommended)

    **Features:**
    - Automatic image optimization (resize + compress)
    - Decentralized storage via IPFS
    - Permanent file hosting through Lighthouse pinning
    - CDN-like access via Lighthouse gateway

    **Limits:**
    - Maximum file size: 50 MB (configurable)
    - Images automatically resized to max 1920x1080
    - JPEG quality: 85 (configurable)

    **Returns:**
    - IPFS hash (CID) for permanent reference
    - Gateway URL for browser access
    - File metadata (size, type, name)

    **Example Response:**
    ```json
    {
      "success": true,
      "ipfs_hash": "QmX7Vd...",
      "ipfs_url": "https://gateway.lighthouse.storage/ipfs/QmX7Vd...",
      "file_name": "avatar.jpg",
      "file_size": 245678,
      "mime_type": "image/jpeg"
    }
    ```
    """
    try:
        result = await media_service.upload_to_ipfs(file, optimize_images=optimize)
        return result

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IPFSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except StorageError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.delete("/unpin", response_model=MediaDeleteResponse)
async def unpin_media(
    delete_request: MediaDeleteRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Unpin file from Lighthouse pinning service

    **Important Notes:**
    - Files on IPFS are permanent and cannot be truly "deleted"
    - This endpoint only removes the file from OUR pinning service
    - The file may still be accessible if pinned by other IPFS nodes
    - Use this to reduce storage costs for unused files

    **Permissions:**
    - Only the file uploader or moderators can unpin files
    - System automatically unpins files flagged for removal

    **Args:**
    - ipfs_hash: IPFS CID of the file to unpin

    **Returns:**
    - Success status
    - Explanatory message about IPFS permanence
    """
    try:
        success = await media_service.unpin_from_ipfs(delete_request.ipfs_hash)

        if success:
            return MediaDeleteResponse(
                success=True, message=f"File {delete_request.ipfs_hash} unpinned successfully"
            )
        else:
            return MediaDeleteResponse(
                success=False, message=f"Failed to unpin {delete_request.ipfs_hash}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unpin failed: {str(e)}",
        )


@router.get("/info/{ipfs_hash}")
async def get_media_info(ipfs_hash: str):
    """Get media file information from IPFS hash

    Returns the gateway URL and metadata for an IPFS hash.

    **Args:**
    - ipfs_hash: IPFS CID

    **Returns:**
    - Gateway URL for accessing the file
    - IPFS hash
    """
    gateway_url = f"{media_service.gateway_url}{ipfs_hash}"

    return {
        "ipfs_hash": ipfs_hash,
        "gateway_url": gateway_url,
        "protocol": "ipfs",
        "note": "File is permanently stored on IPFS network",
    }
