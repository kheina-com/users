from pydantic import BaseModel


class UpdateSelf(BaseModel) :
	name: str
	handle: str
	privacy: str
	icon: str
	website: str
	description: str
