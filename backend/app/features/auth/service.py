import logging
import uuid

from app.core.audit import AuditAction, audit_logger
from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError, ValidationError
from app.core.security.jwt import jwt_handler
from app.core.security.password import password_hasher
from app.domain.entities.user import User, UserRole
from app.features.auth.repository import RefreshTokenRepository, UserRepository
from app.features.auth.schemas import TokenResponse, UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo

    async def login(
        self,
        username: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        remember_me: bool = False,
    ) -> tuple[TokenResponse, str, User]:
        logger.info("Login attempt for user: %s", username)

        user = await self._user_repo.get_by_username(username)
        if not user:
            audit_logger.log_login(username, ip_address, user_agent, success=False, failure_reason="User not found")
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            audit_logger.log_login(username, ip_address, user_agent, success=False, user_id=user.id, failure_reason="Account disabled")
            raise AuthenticationError("Account is disabled")

        if not password_hasher.verify(password, user.password_hash):
            audit_logger.log_login(username, ip_address, user_agent, success=False, user_id=user.id, failure_reason="Invalid password")
            raise AuthenticationError("Invalid username or password")

        access_token = jwt_handler.create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value, "username": user.username},
        )

        refresh_expire_days = (
            settings.jwt_refresh_token_expire_days_remember
            if remember_me
            else settings.jwt_refresh_token_expire_days
        )
        refresh_token = jwt_handler.create_refresh_token(subject=user.id, expire_days=refresh_expire_days)

        await self._token_repo.create(user.id, refresh_token, refresh_expire_days)
        await self._user_repo.update_last_login(user.id)

        audit_logger.log_login(user.username, ip_address, user_agent, success=True, user_id=user.id)

        token_response = TokenResponse(
            access_token=access_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

        return token_response, refresh_token, user

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: str | None = None,
    ) -> tuple[TokenResponse, str]:
        logger.info("Token refresh attempt")

        user_id = await self._token_repo.validate(refresh_token)
        if not user_id:
            raise AuthenticationError("Invalid or expired refresh token")

        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        await self._token_repo.revoke(refresh_token)

        new_access = jwt_handler.create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value, "username": user.username},
        )
        new_refresh = jwt_handler.create_refresh_token(subject=user.id)

        await self._token_repo.create(user.id, new_refresh, settings.jwt_refresh_token_expire_days)

        audit_logger.log(
            AuditAction.TOKEN_REFRESH,
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
        )

        return TokenResponse(
            access_token=new_access,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        ), new_refresh

    async def logout(
        self,
        refresh_token: str,
        user_id: str,
        username: str,
        ip_address: str | None = None,
    ) -> None:
        logger.info("Logout for user: %s", username)

        await self._token_repo.revoke(refresh_token)

        audit_logger.log(
            AuditAction.LOGOUT,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        ip_address: str | None = None,
    ) -> UserResponse:
        logger.info("Registration attempt for: %s", username)

        existing = await self._user_repo.get_by_username(username)
        if existing:
            raise ValidationError("Username already exists", field="username")

        existing_email = await self._user_repo.get_by_email(email)
        if existing_email:
            raise ValidationError("Email already registered", field="email")

        user_id = str(uuid.uuid4())
        hashed = password_hasher.hash(password)

        user = await self._user_repo.create(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=hashed,
            role=UserRole.VIEWER,
        )

        audit_logger.log(
            AuditAction.USER_CREATE,
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            resource_type="user",
            resource_id=user.id,
        )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
        )

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
        ip_address: str | None = None,
    ) -> None:
        logger.info("Password change for user: %s", user_id)

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        if not password_hasher.verify(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        new_hash = password_hasher.hash(new_password)
        await self._user_repo.update_password(user_id, new_hash)

        await self._token_repo.revoke_all_for_user(user_id)

        audit_logger.log(
            AuditAction.PASSWORD_CHANGE,
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
        )

    async def get_current_user(self, user_id: str) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        if not user.is_active:
            raise AuthorizationError("Account is disabled")
        return user
