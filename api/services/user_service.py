"""
ユーザーサービスモジュール

このモジュールは、ユーザー管理を行うサービスを提供します。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..auth.password import get_password_hash, verify_password
from ..database import _get_db_context
from ..models.user import User


class UserService:
    """ユーザーサービスクラス"""

    async def create_user(
        self, username: str, email: str, password: str, is_admin: bool = False, db=None
    ) -> Optional[Dict[str, Any]]:
        """ユーザーを作成

        Args:
            username (str): ユーザー名
            email (str): メールアドレス
            password (str): パスワード
            is_admin (bool, optional): 管理者フラグ。デフォルトはFalse
            db (optional): データベースセッション

        Returns:
            Optional[Dict[str, Any]]: 作成されたユーザー
        """
        if db is None:
            async with _get_db_context() as session:
                return await self.create_user(username, email, password, is_admin, session)

        # ユーザー名またはメールアドレスが既に存在するか確認
        result = await db.execute(select(User).where((User.username == username) | (User.email == email)))
        existing_user = result.scalars().first()

        if existing_user:
            return None

        # パスワードをハッシュ化
        hashed_password = get_password_hash(password)

        # ユーザーを作成
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin=is_admin,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
        }

    async def authenticate_user(self, username: str, password: str, db=None) -> Optional[User]:
        """ユーザーを認証

        Args:
            username (str): ユーザー名
            password (str): パスワード
            db (optional): データベースセッション

        Returns:
            Optional[User]: 認証されたユーザー
        """
        if db is None:
            async with _get_db_context() as session:
                return await self.authenticate_user(username, password, session)

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """ユーザーの詳細を取得

        Args:
            user_id (int): ユーザーID

        Returns:
            Optional[Dict[str, Any]]: ユーザーの詳細
        """
        async with _get_db_context() as db:
            user = await db.get(User, user_id)
            if not user:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """ユーザー名からユーザーを取得

        Args:
            username (str): ユーザー名

        Returns:
            Optional[Dict[str, Any]]: ユーザーの詳細
        """
        async with _get_db_context() as db:
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalars().first()

            if not user:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

    async def list_users(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """ユーザーの一覧を取得

        Args:
            limit (int, optional): 取得件数。デフォルトは10
            offset (int, optional): オフセット。デフォルトは0

        Returns:
            List[Dict[str, Any]]: ユーザーのリスト
        """
        async with _get_db_context() as db:
            result = await db.execute(select(User).order_by(User.id).limit(limit).offset(offset))
            users = result.scalars().all()

            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "is_active": user.is_active,
                }
                for user in users
            ]

    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """ユーザー情報を更新

        Args:
            user_id (int): ユーザーID
            email (Optional[str], optional): メールアドレス。デフォルトはNone
            password (Optional[str], optional): パスワード。デフォルトはNone
            is_active (Optional[bool], optional): アクティブフラグ。デフォルトはNone
            is_admin (Optional[bool], optional): 管理者フラグ。デフォルトはNone

        Returns:
            Optional[Dict[str, Any]]: 更新されたユーザー
        """
        async with _get_db_context() as db:
            user = await db.get(User, user_id)
            if not user:
                return None

            # 更新するフィールドを設定
            if email is not None:
                user.email = email

            if password is not None:
                user.hashed_password = get_password_hash(password)

            if is_active is not None:
                user.is_active = is_active

            if is_admin is not None:
                user.is_admin = is_admin

            await db.commit()
            await db.refresh(user)

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
            }
