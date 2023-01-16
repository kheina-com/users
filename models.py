from datetime import datetime
from typing import List, Optional

from kh_common.base64 import b64encode
from kh_common.models.privacy import UserPrivacy
from kh_common.models.verified import Verified
from kh_common.utilities import int_to_bytes
from pydantic import BaseModel, validator


def int_to_post_id(value: int) -> str :
	if type(value) == int :
		return b64encode(int.to_bytes(value, 6, 'big')).decode()

	return value


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
	_post_id_converter = validator('icon', pre=True, always=True, allow_reuse=True)(int_to_post_id)

	name: str
	handle: str
	privacy: UserPrivacy
	icon: Optional[str]
	verified: Optional[Verified]
	following: Optional[bool]


class User(BaseModel) :
	_post_id_converter = validator('icon', 'banner', pre=True, always=True, allow_reuse=True)(int_to_post_id)

	name: str
	handle: str
	privacy: UserPrivacy
	icon: Optional[str]
	banner: Optional[str]
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
