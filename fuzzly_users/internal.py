from asyncio import Task, ensure_future
from datetime import datetime
from typing import List, Optional

from fuzzly_posts.models import PostId
from kh_common.auth import KhUser
from kh_common.caching import AerospikeCache
from kh_common.caching.key_value_store import KeyValueStore
from kh_common.sql import SqlInterface
from pydantic import BaseModel, validator

from fuzzly_users.models import Badge, User, UserPortable, UserPrivacy, Verified, _post_id_converter


FollowKVS: KeyValueStore = KeyValueStore('kheina', 'following')


class Following(SqlInterface) :

	@AerospikeCache('kheina', 'following', '{user_id}|{target}', _kvs=FollowKVS)
	async def following(self: 'Following', user_id: int, target: int) -> bool :
		"""
		returns true if the user specified by user_id is following the user specified by target
		"""

		data = await self.query_async("""
			SELECT count(1)
			FROM kheina.public.following
			WHERE following.user_id = %s
				AND following.follows = %s;
			""",
			(user_id, target),
			fetch_all=True,
		)

		if not data :
			return False

		return bool(data[0])


Follow: Following = Following()


class InternalUser(BaseModel) :
	_post_id_converter = validator('icon', 'banner', pre=True, always=True, allow_reuse=True)(_post_id_converter)

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
		follow_task: Task[bool] = ensure_future(Follow.following(user.user_id, self.user_id))
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
