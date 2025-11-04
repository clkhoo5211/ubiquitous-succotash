"""Frontend routes for HTML pages

Serves Jinja2 templates for the web UI
"""

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
from src.core.database import AsyncSessionLocal

router = APIRouter()


# Template helper function
async def get_template_context(request: Request):
    """Get default template context for all pages"""
    from src.core.database import get_db
    from src.core.session import get_session
    from src.models.user import User
    from sqlalchemy import select

    current_user = None

    try:
        # Get session ID from cookie
        session_id = request.cookies.get("session_id")

        if session_id:
            # Get user_id from Redis session
            user_id = await get_session(session_id)

            if user_id:
                # Get database session
                async for db in get_db():
                    # Fetch user from database
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user and user.is_active and not user.is_banned:
                        current_user = user
                    break
    except Exception:
        current_user = None

    return {
        "request": request,
        "current_user": current_user,
    }


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request, filter: Optional[str] = None, page: int = 1):
    """Home page - show latest posts"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal
    from src.services.post_service import PostService
    from src.models.organization import Channel
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get posts
        post_service = PostService(db)
        posts, total = await post_service.list_posts(page=page, page_size=20)

        # Apply filter if specified
        if filter == "hot":
            # Sort by highest likes
            posts = sorted(posts, key=lambda p: p.like_count, reverse=True)
        elif filter == "new":
            # Already sorted by newest (default)
            pass
        elif filter == "top":
            # Sort by most comments
            posts = sorted(posts, key=lambda p: p.comment_count, reverse=True)

        # Get channels
        result = await db.execute(select(Channel))
        channels = result.scalars().all()

        import math

        context = await get_template_context(request)
        context.update(
            {
                "posts": posts,
                "channels": channels,
                "top_users": [],
                "total_posts": total,
                "total_pages": math.ceil(total / 20) if total > 0 else 1,
                "current_page": page,
                "current_filter": filter or "new",
                "stats": {
                    "total_users": 0,
                    "total_posts": total,
                    "total_comments": 0,
                    "active_today": 0,
                },
            }
        )

    return templates.TemplateResponse("index.html", context)


@router.get("/explore", response_class=HTMLResponse, include_in_schema=False)
async def explore(request: Request, filter: Optional[str] = None, page: int = 1):
    """Explore page - browse all posts"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal
    from src.services.post_service import PostService
    from src.models.organization import Channel
    from sqlalchemy import select

    # Get real posts from database
    async with AsyncSessionLocal() as db:
        post_service = PostService(db)
        posts, total_count = await post_service.list_posts(page=page, page_size=50)

        # Apply filter if specified
        if filter == "hot":
            # Sort by highest likes
            posts = sorted(posts, key=lambda p: p.like_count if p.like_count else 0, reverse=True)
        elif filter == "new":
            # Already sorted by newest (default)
            pass
        elif filter == "top":
            # Sort by most comments
            posts = sorted(
                posts, key=lambda p: p.comment_count if p.comment_count else 0, reverse=True
            )

        # Get channels
        result = await db.execute(select(Channel))
        channels = result.scalars().all()

        # Calculate stats
        from sqlalchemy import select, func
        from src.models.user import User
        from src.models.content import Post, Comment

        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        total_posts_result = await db.execute(select(func.count(Post.id)))
        total_posts = total_posts_result.scalar() or 0

        total_comments_result = await db.execute(select(func.count(Comment.id)))
        total_comments = total_comments_result.scalar() or 0

    context = await get_template_context(request)
    context.update(
        {
            "posts": posts,
            "channels": channels,
            "current_filter": filter or "all",
            "top_users": [],
            "stats": {
                "total_users": total_users,
                "total_posts": total_posts,
                "total_comments": total_comments,
                "active_today": 0,
                "bnb_distributed": 0,
            },
        }
    )

    return templates.TemplateResponse("explore.html", context)


@router.get("/channel/{slug}", response_class=HTMLResponse, include_in_schema=False)
async def channel_page(request: Request, slug: str, filter: Optional[str] = None, page: int = 1):
    """Channel page - show posts for a specific channel"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal
    from src.services.post_service import PostService
    from src.models.organization import Channel
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get channel by slug
        result = await db.execute(select(Channel).where(Channel.slug == slug))
        channel = result.scalar_one_or_none()

        if not channel:
            return RedirectResponse(url="/explore?error=Channel+not+found", status_code=303)

        # Get posts for this channel
        post_service = PostService(db)
        posts, total = await post_service.list_posts(page=page, page_size=20, channel_id=channel.id)

        # Apply filter if specified
        if filter == "hot":
            posts = sorted(posts, key=lambda p: p.like_count if p.like_count else 0, reverse=True)
        elif filter == "new":
            pass  # Already sorted by newest
        elif filter == "top":
            posts = sorted(
                posts, key=lambda p: p.comment_count if p.comment_count else 0, reverse=True
            )

        # Get all channels for sidebar
        all_channels = await db.execute(select(Channel))
        channels = all_channels.scalars().all()

        import math

        context = await get_template_context(request)
        context.update(
            {
                "channel": channel,
                "posts": posts,
                "channels": channels,
                "current_filter": filter or "new",
                "total_posts": total,
                "total_pages": math.ceil(total / 20) if total > 0 else 1,
                "current_page": page,
                "top_users": [],
                "stats": {
                    "total_users": 0,
                    "total_posts": total,
                    "total_comments": 0,
                    "active_today": 0,
                },
            }
        )

    return templates.TemplateResponse("explore.html", context)


@router.get("/channels", response_class=HTMLResponse, include_in_schema=False)
async def channels_list(request: Request):
    """Channels list page - show all posts (all channels)"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal
    from src.services.post_service import PostService
    from src.models.organization import Channel
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get posts from all channels
        post_service = PostService(db)
        posts, total_count = await post_service.list_posts(page=1, page_size=50)

        # Get all channels
        result = await db.execute(select(Channel))
        channels = result.scalars().all()

        context = await get_template_context(request)
        context.update(
            {
                "posts": posts,
                "channels": channels,
                "current_filter": "all",
                "top_users": [],
                "stats": {
                    "total_users": 0,
                    "total_posts": total_count,
                    "total_comments": 0,
                    "active_today": 0,
                    "bnb_distributed": 0,
                },
            }
        )

    return templates.TemplateResponse("explore.html", context)


@router.get("/rewards", response_class=HTMLResponse, include_in_schema=False)
async def rewards(request: Request):
    """Rewards page - view crypto rewards"""
    from src.main import templates

    # Get real user context
    context = await get_template_context(request)

    # Add rewards-specific data
    context.update(
        {
            "conversion_rate": 10000,  # Default: 10,000 points = 1 BNB
            "min_conversion": 10000,  # Minimum points to convert
        }
    )

    return templates.TemplateResponse("rewards/crypto.html", context)


@router.get("/leaderboard", response_class=HTMLResponse, include_in_schema=False)
async def leaderboard(request: Request):
    """Leaderboard page - show top users by contribution"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal
    from src.models.user import User
    from src.models.organization import Channel
    from src.models.content import Post, Comment
    from sqlalchemy import select, desc, func

    async with AsyncSessionLocal() as db:
        # Get users with contribution statistics (posts + comments count)
        # Calculate contribution score as total posts + total comments
        result = await db.execute(
            select(
                User.id,
                User.username,
                User.display_name,
                User.avatar_url,
                func.coalesce(func.count(Post.id), 0).label("post_count"),
                func.coalesce(func.count(Comment.id), 0).label("comment_count"),
            )
            .outerjoin(Post, User.id == Post.user_id)
            .outerjoin(Comment, User.id == Comment.user_id)
            .where(User.is_active)
            .where(~User.is_banned)
            .group_by(User.id)
            .having(
                func.coalesce(func.count(Post.id), 0) + func.coalesce(func.count(Comment.id), 0) > 0
            )
            .order_by(
                desc(
                    func.coalesce(func.count(Post.id), 0) + func.coalesce(func.count(Comment.id), 0)
                )
            )
            .limit(50)
        )

        top_users_data = []
        for row in result.all():
            contribution_score = row.post_count + row.comment_count
            top_users_data.append(
                {
                    "username": row.username,
                    "display_name": row.display_name,
                    "avatar_url": row.avatar_url,
                    "post_count": row.post_count,
                    "comment_count": row.comment_count,
                    "contribution_score": contribution_score,
                }
            )

        # Get channels for sidebar
        channels_result = await db.execute(select(Channel))
        channels = channels_result.scalars().all()

        # Get stats
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        total_posts_result = await db.execute(select(func.count(Post.id)))
        total_posts = total_posts_result.scalar() or 0

        total_comments_result = await db.execute(select(func.count(Comment.id)))
        total_comments = total_comments_result.scalar() or 0

        context = await get_template_context(request)
        context.update(
            {
                "posts": [],  # Empty posts for leaderboard
                "channels": channels,
                "top_users": top_users_data,  # Pass contribution data instead
                "current_filter": "all",
                "total_posts": total_posts,
                "stats": {
                    "total_users": total_users,
                    "total_posts": total_posts,
                    "total_comments": total_comments,
                    "active_today": 0,
                    "bnb_distributed": 0,
                },
            }
        )

    return templates.TemplateResponse("explore.html", context)


@router.get("/auth/register", response_class=HTMLResponse, include_in_schema=False)
async def register(request: Request):
    """Registration page"""
    from src.main import templates

    return templates.TemplateResponse("auth/register.html", await get_template_context(request))


@router.post("/auth/register", include_in_schema=False)
async def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Handle registration form submission"""
    import httpx

    # Call the API endpoint
    base_url = str(request.base_url).rstrip("/")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v1/auth/register",
                json={"username": username, "email": email, "password": password},
                timeout=10.0,
            )

            if response.status_code == 201:
                # Registration successful - get session cookie from API response
                session_cookie = response.cookies.get("session_id")

                # Create redirect response
                redirect = RedirectResponse(
                    url="/?success=Registration+successful!+Welcome+to+the+forum.", status_code=303
                )

                # Set session cookie if we got one
                if session_cookie:
                    redirect.set_cookie(
                        key="session_id",
                        value=session_cookie,
                        httponly=True,
                        secure=False,
                        samesite="strict",
                        max_age=30 * 24 * 3600,
                    )

                return redirect
            else:
                # Registration failed - redirect back with error
                error_msg = "Registration failed"
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_msg = error_data["detail"]
                    except Exception:
                        pass
                return RedirectResponse(url=f"/auth/register?error={error_msg}", status_code=303)
    except Exception:
        # Error - redirect back
        return RedirectResponse(url="/auth/register?error=Registration+failed", status_code=303)


@router.get("/auth/login", response_class=HTMLResponse, include_in_schema=False)
async def login(request: Request):
    """Login page"""
    from src.main import templates

    return templates.TemplateResponse("auth/login.html", await get_template_context(request))


@router.post("/auth/login", include_in_schema=False)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember_me: Optional[bool] = Form(None),
):
    """Handle login form submission"""
    import httpx
    from fastapi.responses import RedirectResponse

    # Call the API endpoint
    base_url = str(request.base_url).rstrip("/")
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{base_url}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=10.0,
            )

            if response.status_code == 200:
                # Login successful - get session cookie from API response
                session_cookie = response.cookies.get("session_id")

                # Create redirect response
                redirect = RedirectResponse(url="/", status_code=303)

                # Set session cookie if we got one
                if session_cookie:
                    redirect.set_cookie(
                        key="session_id",
                        value=session_cookie,
                        httponly=True,
                        secure=False,  # Set to True in production with HTTPS
                        samesite="strict",
                        max_age=30 * 24 * 3600,  # 30 days
                    )

                return redirect
            else:
                # Login failed - redirect back with error
                return RedirectResponse(
                    url="/auth/login?error=Invalid+credentials", status_code=303
                )
    except Exception:
        # Error - redirect back
        return RedirectResponse(url="/auth/login?error=Login+failed", status_code=303)


@router.get("/profile/{username}", response_class=HTMLResponse, include_in_schema=False)
async def profile(request: Request, username: str):
    """User profile page"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal
    from src.services.user_service import UserService
    from src.services.post_service import PostService

    async with AsyncSessionLocal() as db:
        try:
            # Get user by username
            user_service = UserService(db)
            profile_user = await user_service.get_user_by_username(username)

            # Get user's posts
            post_service = PostService(db)
            posts, total_posts = await post_service.list_posts(
                author_id=profile_user.id, page=1, page_size=20
            )

            context = await get_template_context(request)
            context.update(
                {
                    "profile_user": profile_user,
                    "user_posts": posts,
                    "total_posts": total_posts,
                }
            )
        except Exception:
            # User not found
            context = await get_template_context(request)
            context.update(
                {
                    "profile_user": None,
                    "user_posts": [],
                    "total_posts": 0,
                }
            )

    return templates.TemplateResponse("profile/view.html", context)


@router.get("/posts/create", response_class=HTMLResponse, include_in_schema=False)
async def create_post(request: Request):
    """Create post page"""
    from src.main import templates

    return templates.TemplateResponse("posts/create.html", await get_template_context(request))


@router.post("/posts/create", include_in_schema=False)
async def create_post_post(
    request: Request,
    title: str = Form(...),
    body: str = Form(...),
    channel_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    media: List[UploadFile] = File(default=[]),
):
    """Handle post creation form submission with media support"""

    try:
        # Get current user from session
        context = await get_template_context(request)
        current_user = context.get("current_user")

        if not current_user:
            return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

        # Convert channel_id from string to int, or None if empty
        channel_id_int = None
        if channel_id and channel_id.strip():
            try:
                channel_id_int = int(channel_id)
            except ValueError:
                channel_id_int = None

        # Create post directly using the service
        from src.core.database import get_db
        from src.services.post_service import PostService
        from src.services.file_upload_service import FileUploadService
        from src.schemas.post import PostCreate

        post_data = PostCreate(
            title=title,
            body=body,
            channel_id=channel_id_int,
        )

        async for db in get_db():
            # Create post first
            post_service = PostService(db)
            new_post = await post_service.create_post(post_data, current_user.id)

            # Handle media uploads if provided
            if media and len(media) > 0 and media[0].filename:
                file_upload_service = FileUploadService(db)
                for file in media:
                    if file.filename:  # Only process if file was uploaded
                        await file_upload_service.upload_file(file, current_user.id, new_post.id)

            return RedirectResponse(url=f"/posts/{new_post.id}", status_code=303)
    except Exception as e:
        # Error - redirect back
        import traceback

        traceback.print_exc()
        return RedirectResponse(
            url=f"/posts/create?error=Post+creation+failed: {str(e)}", status_code=303
        )


@router.get("/posts/{post_id}", response_class=HTMLResponse, include_in_schema=False)
async def post_detail(request: Request, post_id: int):
    """Post detail page"""
    from src.main import templates
    from src.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        from src.services.post_service import PostService
        from src.services.comment_service import CommentService

        # Get post with all details
        post_service = PostService(db)
        post = await post_service.get_post_by_id(post_id, increment_view=True)

        # Get comments for the post
        comment_service = CommentService(db)
        comments, _ = await comment_service.list_comments(post_id, page=1, page_size=50)

        # Get media attachments for the post
        from src.services.file_upload_service import FileUploadService

        file_upload_service = FileUploadService(db)
        media_attachments = await file_upload_service.get_media_by_post(post_id)

        # Get template context
        context = await get_template_context(request)
        current_user = context.get("current_user")

        # Check if current user has liked the post
        user_has_liked = False
        if current_user:
            from src.models.content import Like
            from sqlalchemy import select, and_

            like_result = await db.execute(
                select(Like).where(and_(Like.post_id == post_id, Like.user_id == current_user.id))
            )
            user_has_liked = like_result.scalar_one_or_none() is not None

        return templates.TemplateResponse(
            "posts/detail.html",
            {
                **context,
                "post": post,
                "comments": comments,
                "media_attachments": media_attachments,
                "user_has_liked": user_has_liked,
            },
        )


@router.post("/posts/{post_id}/comments", include_in_schema=False)
async def create_comment_post(
    request: Request,
    post_id: int,
    body: str = Form(...),
    parent_id: Optional[int] = Form(None),
):
    """Handle comment form submission"""

    try:
        # Get current user from session
        context = await get_template_context(request)
        current_user = context.get("current_user")

        if not current_user:
            return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

        # Create comment directly using the service
        from src.services.comment_service import CommentService
        from src.schemas.comment import CommentCreate

        comment_data = CommentCreate(
            body=body,
            parent_id=parent_id,
        )

        async with AsyncSessionLocal() as db:
            comment_service = CommentService(db)
            new_comment = await comment_service.create_comment(
                post_id, comment_data, current_user.id
            )

            return RedirectResponse(
                url=f"/posts/{post_id}#comment-{new_comment.id}", status_code=303
            )
    except Exception as e:
        # Error - redirect back
        import traceback

        traceback.print_exc()
        return RedirectResponse(
            url=f"/posts/{post_id}?error=Comment+failed: {str(e)}", status_code=303
        )


@router.post("/posts/{post_id}/like", include_in_schema=False)
async def like_post_handler(
    request: Request,
    post_id: int,
):
    """Handle like post action"""

    try:
        # Get current user from session
        context = await get_template_context(request)
        current_user = context.get("current_user")

        if not current_user:
            return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

        # Like post using the service
        from src.services.like_service import LikeService

        async with AsyncSessionLocal() as db:
            like_service = LikeService(db)
            await like_service.like_post(post_id, current_user.id)

            return RedirectResponse(url=f"/posts/{post_id}", status_code=303)
    except Exception as e:
        # Error - redirect back
        import traceback

        traceback.print_exc()
        return RedirectResponse(
            url=f"/posts/{post_id}?error=Like+failed: {str(e)}", status_code=303
        )


@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    """Settings page"""
    from src.main import templates

    context = await get_template_context(request)

    # Require authentication
    if not context.get("current_user"):
        return RedirectResponse(
            url="/auth/login?error=Please+login+to+access+settings", status_code=303
        )

    return templates.TemplateResponse("settings.html", context)


@router.post("/settings/profile", include_in_schema=False)
async def update_profile(
    request: Request,
    username: str = Form(...),
    display_name: Optional[str] = Form(None),
    email: str = Form(...),
    bio: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
):
    """Update user profile"""
    context = await get_template_context(request)
    current_user = context.get("current_user")

    if not current_user:
        return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

    try:
        async with AsyncSessionLocal() as db:
            from src.models.user import User
            from sqlalchemy import select

            # Get user from database
            result = await db.execute(select(User).where(User.id == current_user.id))
            user = result.scalar_one()

            # Update fields
            user.username = username
            user.display_name = display_name if display_name else None
            user.email = email
            user.bio = bio if bio else None
            user.website = website if website else None

            await db.commit()

            return RedirectResponse(
                url="/settings?success=Profile+updated+successfully", status_code=303
            )
    except Exception as e:
        return RedirectResponse(
            url=f"/settings?error=Failed+to+update+profile: {str(e)}", status_code=303
        )


@router.post("/settings/password", include_in_schema=False)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Change user password"""
    context = await get_template_context(request)
    current_user = context.get("current_user")

    if not current_user:
        return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

    if new_password != confirm_password:
        return RedirectResponse(url="/settings?error=Passwords+do+not+match", status_code=303)

    try:
        async with AsyncSessionLocal() as db:
            from src.models.user import User
            from src.core.security import verify_password, hash_password
            from sqlalchemy import select

            # Get user from database
            result = await db.execute(select(User).where(User.id == current_user.id))
            user = result.scalar_one()

            # Verify current password
            if not verify_password(current_password, user.password_hash):
                return RedirectResponse(
                    url="/settings?error=Current+password+is+incorrect", status_code=303
                )

            # Update password
            user.password_hash = hash_password(new_password)
            await db.commit()

            return RedirectResponse(
                url="/settings?success=Password+changed+successfully", status_code=303
            )
    except Exception as e:
        return RedirectResponse(
            url=f"/settings?error=Failed+to+change+password: {str(e)}", status_code=303
        )


@router.post("/settings/wallet", include_in_schema=False)
async def update_wallet(
    request: Request,
    bnb_wallet: Optional[str] = Form(None),
):
    """Update BNB wallet address"""
    context = await get_template_context(request)
    current_user = context.get("current_user")

    if not current_user:
        return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

    try:
        async with AsyncSessionLocal() as db:
            from src.models.user import User
            from sqlalchemy import select

            # Get user from database
            result = await db.execute(select(User).where(User.id == current_user.id))
            user = result.scalar_one()

            # Update wallet address
            user.bnb_wallet_address = bnb_wallet if bnb_wallet else None
            await db.commit()

            return RedirectResponse(
                url="/settings?success=Wallet+address+updated+successfully", status_code=303
            )
    except Exception as e:
        return RedirectResponse(
            url=f"/settings?error=Failed+to+update+wallet: {str(e)}", status_code=303
        )


@router.post("/settings/notifications", include_in_schema=False)
async def update_notifications(
    request: Request,
    email_notifications: Optional[str] = Form(None),
    push_notifications: Optional[str] = Form(None),
):
    """Update notification settings"""
    context = await get_template_context(request)
    current_user = context.get("current_user")

    if not current_user:
        return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

    try:
        async with AsyncSessionLocal() as db:
            from src.models.user import User
            from sqlalchemy import select

            # Get user from database
            result = await db.execute(select(User).where(User.id == current_user.id))
            user = result.scalar_one()

            # Update notification settings
            user.email_notifications = email_notifications == "true"
            user.push_notifications = push_notifications == "true"
            await db.commit()

            return RedirectResponse(
                url="/settings?success=Notification+settings+updated+successfully", status_code=303
            )
    except Exception as e:
        return RedirectResponse(
            url=f"/settings?error=Failed+to+update+notifications: {str(e)}", status_code=303
        )


@router.post("/settings/delete-account", include_in_schema=False)
async def delete_account(request: Request):
    """Delete user account"""
    context = await get_template_context(request)
    current_user = context.get("current_user")

    if not current_user:
        return RedirectResponse(url="/auth/login?error=Not+authenticated", status_code=303)

    try:
        async with AsyncSessionLocal() as db:
            from src.models.user import User
            from sqlalchemy import select

            # Get user from database
            result = await db.execute(select(User).where(User.id == current_user.id))
            user = result.scalar_one()

            # Soft delete - mark as inactive
            user.is_active = False
            await db.commit()

            # Logout user
            resp = RedirectResponse(url="/auth/logout", status_code=303)
            return resp
    except Exception as e:
        return RedirectResponse(
            url=f"/settings?error=Failed+to+delete+account: {str(e)}", status_code=303
        )


@router.get("/auth/logout", include_in_schema=False)
async def logout_get(request: Request):
    """Handle logout GET request"""
    import httpx

    try:
        # Call the API logout endpoint
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/api/v1/auth/logout", cookies=request.cookies)

        # Create response and delete session cookie
        resp = RedirectResponse(url="/", status_code=303)
        resp.delete_cookie(key="session_id")

        return resp
    except Exception:
        # If logout fails, still delete cookie and redirect
        resp = RedirectResponse(url="/", status_code=303)
        resp.delete_cookie(key="session_id")
        return resp
