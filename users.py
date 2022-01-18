from kh_common.exceptions.http_error import BadRequest, HttpErrorHandler, NotFound, UnprocessableEntity
from kh_common.caching import ArgsCache, SimpleCache
from kh_common.models.privacy import UserPrivacy
from kh_common.models.verified import Verified
from kh_common.hashing import Hashable
from kh_common.sql import SqlInterface
from kh_common.auth import KhUser
from models import Badge, User
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


	@SimpleCache(600)
	def _get_privacy_map(self) -> Dict[str, UserPrivacy] :
		data = self.query("""
			SELECT privacy_id, type
			FROM kheina.public.privacy;
			""",
			fetch_all=True,
		)
		return { x[0]: UserPrivacy[x[1]] for x in data if x[1] in UserPrivacy.__members__ }


	@SimpleCache(600)
	def _get_badge_map(self) -> Dict[int, Badge] :
		data = self.query("""
			SELECT badge_id, emoji, label
			FROM kheina.public.badges;
			""",
			fetch_all=True,
		)
		return { x[0]: Badge(emoji=x[1], label=x[2]) for x in data }


	@SimpleCache(600)
	def _get_reverse_badge_map(self) -> Dict[Badge, int] :
		return { (badge.emoji, badge.label): id for id, badge in self._get_badge_map().items() }


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
				users.banner,
				users.mod,
				users.admin,
				users.verified,
				array_agg(user_badge.badge_id)
			FROM kheina.public.users
				LEFT JOIN kheina.public.user_badge
					ON user_badge.user_id = users.user_id
			WHERE lower(users.handle) = %s
			GROUP BY
				users.handle,
				users.display_name,
				users.privacy_id,
				users.icon,
				users.website,
				users.created_on,
				users.description,
				users.banner,
				users.mod,
				users.admin,
				users.verified;
			""",
			(handle.lower(),),
			fetch_one=True,
		)

		if data :
			verified = None

			if data[9] :
				verified = Verified.admin

			elif data[8] :
				verified = Verified.mod

			elif data[10] :
				verified = Verified.artist

			return {
				'name': data[0],
				'handle': data[1],
				'privacy': self._get_privacy_map()[data[2]],
				'icon': data[3],
				'banner': data[7],
				'website': data[4],
				'created': data[5],
				'description': data[6],
				'verified': verified,
				'badges': list(filter(None, map(self._get_badge_map().get, data[11]))),
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
				users.banner,
				users.mod,
				users.admin,
				users.verified,
				array_agg(user_badge.badge_id)
			FROM kheina.public.users
				LEFT JOIN kheina.public.user_badge
					ON user_badge.user_id = users.user_id
			WHERE users.user_id = %s
			GROUP BY
				users.user_id,
				users.handle,
				users.display_name,
				users.privacy_id,
				users.icon,
				users.website,
				users.created_on,
				users.description,
				users.banner,
				users.mod,
				users.admin,
				users.verified;
			""",
			(user.user_id,),
			fetch_one=True,
		)

		verified = None

		if data[9] :
			verified = Verified.admin

		elif data[8] :
			verified = Verified.mod

		elif data[10] :
			verified = Verified.artist

		return User(
			name = data[0],
			handle = data[1],
			privacy = self._get_privacy_map()[data[2]],
			icon = data[3],
			banner = data[7],
			website = data[4],
			created = data[5],
			description = data[6],
			verified = verified,
			badges = list(filter(None, map(self._get_badge_map().get, data[11]))),
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
				users.banner,
				users.mod,
				users.admin,
				users.verified,
				array_agg(user_badge.badge_id)
			FROM kheina.public.users
				LEFT JOIN kheina.public.user_badge
					ON user_badge.user_id = users.user_id
			GROUP BY
				users.handle,
				users.display_name,
				users.privacy_id,
				users.icon,
				users.website,
				users.created_on,
				users.description,
				users.banner,
				users.mod,
				users.admin,
				users.verified;
			""",
			fetch_all=True,
		)

		return [
			User(
				name = row[0],
				handle = row[1],
				privacy = self._get_privacy_map()[row[2]],
				icon = row[3],
				banner = row[7],
				website = row[4],
				created = row[5],
				description = row[6],
				following = row[1].lower() in self._get_followers(user.user_id),
				badges = list(filter(None, map(self._get_badge_map().get, row[11]))),
				verified = Verified.admin if row[9] else (
					Verified.mod if row[8] else (
						Verified.artist if row[10] else None
					)
				),
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


	@ArgsCache(30)
	@HttpErrorHandler('adding badge to self')
	async def addBadge(self, user: KhUser, emoji: str, label: str) -> None :
		badge_id = self._get_reverse_badge_map().get((emoji, label))

		if not badge_id :
			raise UnprocessableEntity(f'badge with emoji "{emoji}" and label "{label}" was not found.')

		await self.query_async("""
			INSERT INTO kheina.public.user_badge
			(user_id, badge_id)
			VALUES
			(%s, %s);
			""",
			(user.user_id, badge_id),
			commit=True,
		)


	@ArgsCache(30)
	@HttpErrorHandler('removing badge from self')
	async def removeBadge(self, user: KhUser, emoji: str, label: str) -> None :
		badge_id = self._get_reverse_badge_map().get((emoji, label))

		if not badge_id :
			raise UnprocessableEntity(f'badge with emoji "{emoji}" and label "{label}" was not found.')

		await self.query_async("""
			DELETE FROM kheina.public.user_badge
				WHERE user_id = %s
					AND badge_id = %s;
			""",
			(user.user_id, badge_id),
			commit=True,
		)


	@HttpErrorHandler('creating badge')
	async def createBadge(self, emoji: str, label: str) -> None :
		await self.query_async("""
			INSERT INTO kheina.public.badges
			(emoji, label)
			VALUES
			(%s, %s);
			""",
			(emoji, label),
			commit=True,
		)


	@HttpErrorHandler('verifying user')
	async def verifyUser(self, handle: str, verified: Verified) -> None :
		await self.query_async(f"""
			UPDATE kheina.public.users
				set {'verified' if verified == Verified.artist else verified.name} = true
			WHERE LOWER(handle) = %s;
			""",
			(handle.lower(),),
			commit=True,
		)
