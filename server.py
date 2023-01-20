from typing import List

from kh_common.models.auth import Scope
from kh_common.server import NoContentResponse, Request, ServerApp

from fuzzly_users.internal import InternalUser
from fuzzly_users.models import Badge, Follow, SetMod, SetVerified, UpdateSelf, User
from users import Users


app = ServerApp(
	auth_required = False,
	allowed_hosts = [
		'localhost',
		'127.0.0.1',
		'*.kheina.com',
		'kheina.com',
		'*.fuzz.ly',
		'fuzz.ly',
	],
	allowed_origins = [
		'localhost',
		'127.0.0.1',
		'dev.kheina.com',
		'kheina.com',
		'dev.fuzz.ly',
		'fuzz.ly',
	],
)
users: Users = Users()


@app.on_event('shutdown')
async def shutdown() :
	users.close()


################################################## INTERNAL ##################################################
@app.get('/i1/user/{user_id}', responses={ 200: { 'model': InternalUser } })
async def i1User(req: Request, user_id: int) :
	await req.user.verify_user(Scope.internal)
	return await users._get_user(user_id)


##################################################  PUBLIC  ##################################################
@app.get('/v1/fetch_user/{handle}', responses={ 200: { 'model': User } })
@app.get('/v1/user/{handle}', responses={ 200: { 'model': User } })
async def v1User(req: Request, handle: str) :
	return users.getUser(req.user, handle)


@app.get('/v1/fetch_self', responses={ 200: { 'model': User } })
async def v1FetchSelf(req: Request) -> User :
	await req.user.authenticated()
	return users.getSelf(req.user)


@app.post('/v1/update_self', responses={ 204: { 'model': None } }, status_code=204)
async def v1UpdateSelf(req: Request, body: UpdateSelf) -> None :
	await req.user.authenticated()

	users.updateSelf(
		req.user,
		body.name,
		body.privacy,
		body.icon,
		body.website,
		body.description,
	)

	return NoContentResponse


@app.post('/v1/follow_user', responses={ 204: { 'model': None } }, status_code=204)
async def v1FollowUser(req: Request, body: Follow) :
	await req.user.authenticated()
	users.followUser(req.user, body.handle)
	return NoContentResponse


@app.post('/v1/unfollow_user', responses={ 204: { 'model': None } }, status_code=204)
async def v1UnfollowUser(req: Request, body: Follow) :
	await req.user.authenticated()
	users.unfollowUser(req.user, body.handle)
	return NoContentResponse


@app.get('/v1/all_users', responses={ 200: { 'model': List[User] } })
async def v1FetchUsers(req: Request) -> List[User] :
	await req.user.verify_scope(Scope.admin)
	return users.getUsers(req.user)


@app.post('/v1/set_mod', responses={ 204: { 'model': None } }, status_code=204)
async def v1SetMod(req: Request, body: SetMod) -> None :
	await req.user.verify_scope(Scope.admin)
	users.setMod(body.handle, body.mod)
	return NoContentResponse


@app.post('/v1/set_verified', responses={ 204: { 'model': None } }, status_code=204)
async def v1Verify(req: Request, body: SetVerified) -> None :
	await req.user.verify_scope(Scope.admin)
	await users.verifyUser(body.handle, body.verified)
	return NoContentResponse


@app.get('/v1/badges', responses={ 200: { 'model': List[Badge] } })
async def v1Badges() -> List[Badge] :
	return await users.fetchBadges()


@app.post('/v1/add_badge', responses={ 204: { 'model': None } }, status_code=204)
async def v1AddBadge(req: Request, body: Badge) -> None :
	await req.user.authenticated()
	await users.addBadge(req.user, body.emoji, body.label)
	return NoContentResponse


@app.post('/v1/remove_badge', responses={ 204: { 'model': None } }, status_code=204)
async def v1RemoveBadge(req: Request, body: Badge) -> None :
	await req.user.authenticated()
	await users.removeBadge(req.user, body.emoji, body.label)
	return NoContentResponse


@app.post('/v1/create_badge', responses={ 204: { 'model': None } }, status_code=204)
async def v1CreateBadge(req: Request, body: Badge) -> None :
	await req.user.verify_scope(Scope.admin)
	await users.createBadge(body.emoji, body.label)
	return NoContentResponse


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='0.0.0.0', port=5005)
