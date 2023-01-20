from kh_common.gateway import Gateway
from kh_common.client import Client

from fuzzly_users.constants import Host
from fuzzly_users.internal import InternalUser
from fuzzly_users.models import User


class UserClient(Client) :

	def __init__(self: 'UserClient', *a, **kv) :
		super().__init__(*a, **kv)
		self._user: Gateway = self.authenticated(Gateway(Host + '/i1/user/{user_id}', InternalUser, method='GET'))
		self.user: Gateway = self.authenticated(Gateway(Host + '/v1/user/{handle}', User, method='GET'))
