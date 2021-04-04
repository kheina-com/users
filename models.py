from pydantic import BaseModel
from enum import Enum, unique


@unique
class Privacy(Enum) :
	public: str = 'public'
	private: str = 'private'


class UpdateSelf(BaseModel) :
	name: str = None
	handle: str = None
	privacy: Privacy = None
	icon: str = None
	website: str = None
	description: str = None
