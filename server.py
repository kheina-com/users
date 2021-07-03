from kh_common.server import NoContentResponse, Request, ServerApp
from models import Follow, SetMod, UpdateSelf
from kh_common.caching import KwargsCache
from kh_common.models.auth import Scope
from kh_common.models.user import User
from typing import List
from users import Users


app = ServerApp(auth_required=False)
users = Users()


@app.on_event('shutdown')
async def shutdown() :
	users.close()


@app.get('/v1/fetch_user/{handle}', responses={ 200: { 'model': User } })
@KwargsCache(5)
async def v1FetchUser(req: Request, handle: str) :
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
	users.followUser(req.user, body.handle)
	return NoContentResponse


@app.post('/v1/unfollow_user', responses={ 204: { 'model': None } }, status_code=204)
async def v1UnfollowUser(req: Request, body: Follow) :
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


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='0.0.0.0', port=5005)
