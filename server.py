from typing import List

from kh_common.models.auth import Scope
from kh_common.server import Request, ServerApp

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
@app.get('/i1/user/{user_id}', response_model=InternalUser)
async def i1User(req: Request, user_id: int) :
	await req.user.verify_user(Scope.internal)
	return await users._get_user(user_id)


##################################################  PUBLIC  ##################################################
@app.get('/v1/fetch_user/{handle}', response_model=User)
@app.get('/v1/user/{handle}', response_model=User)
async def v1User(req: Request, handle: str) :
	return await users.getUser(req.user, handle)


@app.get('/v1/fetch_self', response_model=User)
async def v1FetchSelf(req: Request) -> User :
	await req.user.authenticated()
	return await users.getSelf(req.user)


@app.post('/v1/update_self', status_code=204)
async def v1UpdateSelf(req: Request, body: UpdateSelf) -> None :
	await req.user.authenticated()
	await users.updateSelf(
		req.user,
		body.name,
		body.privacy,
		body.website,
		body.description,
	)


@app.post('/v1/follow_user', status_code=204)
async def v1FollowUser(req: Request, body: Follow) :
	await req.user.authenticated()
	await users.followUser(req.user, body.handle)


@app.post('/v1/unfollow_user', status_code=204)
async def v1UnfollowUser(req: Request, body: Follow) :
	await req.user.authenticated()
	await users.unfollowUser(req.user, body.handle)


@app.get('/v1/all_users', response_model=List[User])
async def v1FetchUsers(req: Request) -> List[User] :
	await req.user.verify_scope(Scope.admin)
	return users.getUsers(req.user)


@app.post('/v1/set_mod', status_code=204)
async def v1SetMod(req: Request, body: SetMod) -> None :
	await req.user.verify_scope(Scope.admin)
	await users.setMod(body.handle, body.mod)


@app.post('/v1/set_verified', status_code=204)
async def v1Verify(req: Request, body: SetVerified) -> None :
	await req.user.verify_scope(Scope.admin)
	await users.verifyUser(body.handle, body.verified)


@app.get('/v1/badges', response_model=List[Badge])
async def v1Badges() -> List[Badge] :
	return await users.fetchBadges()


@app.post('/v1/add_badge', status_code=204)
async def v1AddBadge(req: Request, body: Badge) -> None :
	await req.user.authenticated()
	await users.addBadge(req.user, body)


@app.post('/v1/remove_badge', status_code=204)
async def v1RemoveBadge(req: Request, body: Badge) -> None :
	await req.user.authenticated()
	await users.removeBadge(req.user, body)


@app.post('/v1/create_badge', status_code=204)
async def v1CreateBadge(req: Request, body: Badge) -> None :
	await req.user.verify_scope(Scope.mod)
	await users.createBadge(body)


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='0.0.0.0', port=5005)
