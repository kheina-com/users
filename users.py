from kh_common.exceptions.http_error import BadRequest, HttpErrorHandler, NotFound
from kh_common.caching import ArgsCache
from kh_common.hashing import Hashable
from kh_common.sql import SqlInterface
from kh_common.auth import KhUser
from typing import Dict


class Users(SqlInterface, Hashable) :

	def __init__(self) :
		Hashable.__init__(self)
		SqlInterface.__init__(self)


	def _validatePostId(self, post_id: str) :
		if len(post_id) != 8 :
			raise BadRequest('the given post id is invalid.', logdata={ 'post_id': post_id })


	@ArgsCache(600)
	def _get_privacy_map(self) -> Dict[str, str] :
		data = self.query("""
			SELECT privacy_id, type
			FROM kheina.public.privacy;
			""",
			fetch_all=True,
		)
		return dict(data)


	# cache on endpoint to prevent repeated 404s
	@HttpErrorHandler('retrieving user')
	def getUser(self, handle: str) -> Dict[str, str] :
		data = self.query("""
			SELECT display_name, handle, privacy_id, icon, website, created_on, description
			FROM kheina.public.users
			WHERE handle = %s;
			""",
			(handle,),
			fetch_one=True,
		)

		if data :
			return {
				'name': data[0],
				'handle': data[1],
				'privacy': self._get_privacy_map()[data[2]],
				'icon': data[3],
				'website': data[4],
				'created': str(data[5]),
				'description': data[6],
			}

		else :
			raise NotFound('no data was found for the provided user.')


	@ArgsCache(10)
	@HttpErrorHandler("retrieving user's own profile")
	def getSelf(self, user: KhUser) -> Dict[str, str] :
		data = self.query("""
			SELECT display_name, handle, privacy_id, icon, website, created_on, description
			FROM kheina.public.users
			WHERE user_id = %s;
			""",
			(user.user_id,),
			fetch_one=True,
		)

		return {
			'name': data[0],
			'handle': data[1],
			'privacy': self._get_privacy_map()[data[2]],
			'icon': data[3],
			'website': data[4],
			'created': str(data[5]),
			'description': data[6],
		}


	@HttpErrorHandler('updating user profile')
	def updateSelf(self, user: KhUser, name: str, handle: str, privacy: str, icon: str, website: str, description: str) :		
		updates = []
		params = []

		if name :
			updates.append('display_name = %s')
			params.append(name)

		if handle :
			updates.append('handle = %s')
			params.append(handle)

		if privacy :
			updates.append('privacy_id = privacy_to_id(%s)')
			params.append(privacy)

		if icon :
			self._validatePostId(icon)
			updates.append('icon = %s')
			params.append(icon)

		if website :
			updates.append('website = %s')
			params.append(website)

		if description :
			updates.append('description = %s')
			params.append(description)

		if updates :
			query = f"""
				UPDATE kheina.public.users
				SET {', '.join(updates)}
				WHERE user_id = %s;
				"""
			params.append(user.user_id)

			self.query(query, params, commit=True)

		else :
			raise BadRequest('At least one of the following are required: name, handle, privacy, icon, website, description.')
