from kh_common.models.privacy import UserPrivacy
from pydantic import BaseModel


class UpdateSelf(BaseModel) :
	name: str = None
	privacy: UserPrivacy = None
	icon: str = None
	website: str = None
	description: str = None


class SetMod(BaseModel) :
	handle: str
	mod: bool
