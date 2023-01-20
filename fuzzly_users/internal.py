from asyncio import Task, ensure_future
from fuzzly_users.models import User, UserPortable, UserPrivacy, Verified, Badge
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from fuzzly_posts.models import PostId
from users import Users
from kh_common.auth import KhUser


users: Users = Users()


class InternalUser(BaseModel) :
	user_id: int
	name: str
	handle: str
	privacy: UserPrivacy
	icon: Optional[PostId]
	banner: Optional[PostId]
	website: Optional[str]
	created: datetime
	description: Optional[str]
	verified: Optional[Verified]
	badges: List[Badge]

	async def _following(self: 'InternalUser', user: KhUser) -> bool :
		follow_task: Task[bool] = ensure_future(users._following(user.user_id, self.user_id))
		await user.authenticated()
		return await follow_task

	async def user(self: 'InternalUser', user: Optional[KhUser] = None) -> User :
		following: Optional[bool] = None

		if user :
			following = await self._following(user)

		return User(
			name = self.name,
			handle = self.handle,
			privacy = self.privacy,
			icon = self.icon,
			banner = self.banner,
			website = self.website,
			created = self.created,
			description = self.description,
			verified = self.verified,
			following = following,
			badges = self.badges,
		)

	async def portable(self: 'InternalUser', user: Optional[KhUser] = None) -> UserPortable :
		following: Optional[bool] = None

		if user :
			following = await self._following(user)

		return UserPortable(
			name = self.name,
			handle = self.handle,
			privacy = self.privacy,
			icon = self.icon,
			verified = self.verified,
			following = following,
		)
