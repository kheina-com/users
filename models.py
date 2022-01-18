from kh_common.models.privacy import UserPrivacy
from kh_common.models.verified import Verified
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


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


class User(BaseModel) :
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

	def portable(self) :
		return UserPortable(
			handle = self.handle,
			privacy = self.privacy,
			icon = self.icon,
			verified = self.verified,
			following = self.following,
		)


class UserPortable(BaseModel) :
	name: str
	handle: str
	privacy: UserPrivacy
	icon: Optional[str]
	verified: Optional[Verified]
	following: Optional[bool]
