from datetime import datetime
from enum import Enum, unique
from typing import List, Optional

from fuzzly_posts.models import PostId
from pydantic import BaseModel, validator


def _post_id_converter(value) :
	if value :
		return PostId(value)

	return value


@unique
class UserPrivacy(Enum) :
	public: str = 'public'
	private: str = 'private'


@unique
class Verified(Enum) :
	artist: str = 'artist'
	mod: str = 'mod'
	admin: str = 'admin'


class UpdateSelf(BaseModel) :
	name: str = None
	privacy: UserPrivacy = None
	icon: str = None
	website: str = None
	description: str = None


class SetMod(BaseModel) :
	handle: str
	mod: bool


class SetVerified(BaseModel) :
	handle: str
	verified: Verified


class Follow(BaseModel) :
	handle: str


class Badge(BaseModel) :
	emoji: str
	label: str


class UserPortable(BaseModel) :
	_post_id_converter = validator('icon', pre=True, always=True, allow_reuse=True)(_post_id_converter)

	name: str
	handle: str
	privacy: UserPrivacy
	icon: Optional[PostId]
	verified: Optional[Verified]
	following: Optional[bool]


class User(BaseModel) :
	_post_id_converter = validator('icon', 'banner', pre=True, always=True, allow_reuse=True)(_post_id_converter)

	name: str
	handle: str
	privacy: UserPrivacy
	icon: Optional[PostId]
	banner: Optional[PostId]
	website: Optional[str]
	created: datetime
	description: Optional[str]
	verified: Optional[Verified]
	following: Optional[bool]
	badges: List[Badge]

	def portable(self: 'User') -> UserPortable :
		return UserPortable(
			name = self.name,
			handle = self.handle,
			privacy = self.privacy,
			icon = self.icon,
			verified = self.verified,
			following = self.following,
		)
