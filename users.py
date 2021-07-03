from kh_common.exceptions.http_error import BadRequest, HttpErrorHandler, NotFound
from kh_common.models.privacy import UserPrivacy
from kh_common.models.verified import Verified
from kh_common.caching import ArgsCache
from kh_common.hashing import Hashable
from kh_common.sql import SqlInterface
from kh_common.models.user import User
from kh_common.auth import KhUser
from typing import Dict, Set


class Users(SqlInterface, Hashable) :

	def __init__(self) :
		Hashable.__init__(self)
		SqlInterface.__init__(self)


	def _cleanText(self, text: str) -> str :
		text = text.strip()
		return text if text else None


	def _validatePostId(self, post_id: str) :
		if len(post_id) != 8 :
			raise BadRequest('the given post id is invalid.', post_id=post_id)


	def _validateDescription(self, description: str) :
		if len(description) > 10000 :
			raise BadRequest('the given description is over the 10,000 character limit.', description=description)
		return self._cleanText(description)


	def _validateText(self, text: str) :
		if len(text) > 100 :
			raise BadRequest('the given value is over the 100 character limit.', text=text)
		return self._cleanText(text)


	@ArgsCache(600)
	def _get_privacy_map(self) -> Dict[str, str] :
		data = self.query("""
			SELECT privacy_id, type
			FROM kheina.public.privacy;
			""",
			fetch_all=True,
		)
		return { x[0]: UserPrivacy[x[1]] for x in data if x[1] in UserPrivacy.__members__ }


	@ArgsCache(10)
	def _get_followers(self, user_id) -> Set[str] :
		if not user_id :
			return set()

		data = self.query("""
			SELECT
				users.handle
			FROM kheina.public.following
				INNER JOIN kheina.public.users
					ON users.user_id = following.follows
			WHERE following.user_id = %s;
			""",
			(user_id,),
			fetch_all=True,
		)
		return set(map(lambda x : x[0].lower(), data))


	@ArgsCache(5)
	def _get_user(self, handle: str) -> Dict[str, str] :
		data = self.query("""
			SELECT
				users.display_name,
				users.handle,
				users.privacy_id,
				users.icon,
				users.website,
				users.created_on,
				users.description,
				users.mod,
				users.admin,
				users.verified
			FROM kheina.public.users
			WHERE lower(handle) = %s;
			""",
			(handle.lower(),),
			fetch_one=True,
		)

		if data :
			verified = None

			if data[8] :
				verified = Verified.admin

			elif data[7] :
				verified = Verified.mod

			elif data[9] :
				verified = Verified.artist

			return {
				'name': data[0],
				'handle': data[1],
				'privacy': self._get_privacy_map()[data[2]],
				'icon': data[3],
				'banner': None,
				'website': data[4],
				'created': data[5],
				'description': data[6],
				'verified': verified,
			}

		else :
			raise NotFound('no data was found for the provided user.')


	@HttpErrorHandler('retrieving user')
	def getUser(self, user: KhUser, handle: str) -> User :
		return User(
			following = handle.lower() in self._get_followers(user.user_id),
			**self._get_user(handle),
		)


	@ArgsCache(5)
	def followUser(self, user: KhUser, handle: str) -> None :
		self.query("""
			INSERT INTO kheina.public.following
			(user_id, follows)
			SELECT
				%s,
				users.user_id
			FROM kheina.public.users
			WHERE lower(users.handle) = %s;
			""",
			(
				user.user_id,
				handle.lower(),
			),
			commit=True,
		)


	@ArgsCache(5)
	def unfollowUser(self, user: KhUser, handle: str) -> None :
		self.query("""
			DELETE FROM kheina.public.following
				USING kheina.public.users
			WHERE following.user_id = %s
				AND lower(users.handle) = %s
			""",
			(
				user.user_id,
				handle.lower(),
			),
			commit=True,
		)


	@ArgsCache(5)
	@HttpErrorHandler("retrieving user's own profile")
	def getSelf(self, user: KhUser) -> Dict[str, str] :
		data = self.query("""
			SELECT
				users.display_name,
				users.handle,
				users.privacy_id,
				users.icon,
				users.website,
				users.created_on,
				users.description,
				users.mod,
				users.admin,
				users.verified
			FROM kheina.public.users
			WHERE user_id = %s;
			""",
			(user.user_id,),
			fetch_one=True,
		)

		verified = None

		if data[8] :
			verified = Verified.admin

		elif data[7] :
			verified = Verified.mod

		elif data[9] :
			verified = Verified.artist

		return User(
			name = data[0],
			handle = data[1],
			privacy = self._get_privacy_map()[data[2]],
			icon = data[3],
			banner = None,
			website = data[4],
			created = data[5],
			description = data[6],
			verified = verified,
		)


	@HttpErrorHandler('updating user profile')
	def updateSelf(self, user: KhUser, name: str, privacy: UserPrivacy, icon: str, website: str, description: str) :
		updates = []
		params = []

		if name is not None :
			name = self._validateText(name)
			updates.append('display_name = %s')
			params.append(name)

		if privacy is not None :
			updates.append('privacy_id = privacy_to_id(%s)')
			params.append(privacy.name)

		if icon is not None :
			self._validatePostId(icon)
			updates.append('icon = %s')
			params.append(icon)

		if website is not None :
			website = self._validateText(website)
			updates.append('website = %s')
			params.append(website)

		if description is not None :
			description = self._validateDescription(description)
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


	@HttpErrorHandler('fetching all users')
	def getUsers(self, user: KhUser) :
		data = self.query("""
			SELECT
				users.display_name,
				users.handle,
				users.privacy_id,
				users.icon,
				users.website,
				users.created_on,
				users.description,
				users.mod,
				users.admin,
				users.verified
			FROM kheina.public.users
			""",
			fetch_all=True,
		)

		return [
			User(
				name = row[0],
				handle = row[1],
				privacy = self._get_privacy_map()[row[2]],
				icon = row[3],
				banner = None,
				website = row[4],
				created = row[5],
				description = row[6],
				following = row[1].lower() in self._get_followers(user.user_id),
				verified = Verified.admin if row[8] else (
					Verified.mod if row[7] else (
						Verified.artist if row[9] else None
					)
				)
			)
			for row in data
		]


	@HttpErrorHandler('setting mod')
	def setMod(self, handle: str, mod: bool) :
		self.query("""
			UPDATE kheina.public.users
				SET mod = %s
			WHERE handle = %s
			""",
			(mod, handle),
			commit=True,
		)
