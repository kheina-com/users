from kh_common.caching import AerospikeCache
from kh_common.client import Client
from kh_common.gateway import Gateway

from fuzzly_users.constants import Host
from fuzzly_users.internal import InternalUser
from fuzzly_users.models import User


class UserClient(Client) :

	def __init__(self: 'UserClient', *a, internal=False, **kv) :
		super().__init__(*a, **kv)
		self._user: Gateway = None
		self.user: Gateway = self.authenticated(Gateway(Host + '/v1/user/{handle}', User, method='GET'))

		if internal :
			self._user = AerospikeCache('kheina', 'users', '{user_id}', read_only=True)(self.authenticated(Gateway(Host + '/i1/user/{user_id}', InternalUser, method='GET')))
