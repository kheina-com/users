from kh_common.server import JsonResponse, NoContentResponse, Request, ServerApp
from kh_common.caching import KwargsCache
from kh_common.models.auth import Scope
from fastapi.responses import Response
from models import SetMod, UpdateSelf
from users import Users


app = ServerApp(auth_required=False)
users = Users()


@app.on_event('shutdown')
async def shutdown() :
	users.close()


@app.get('/v1/fetch_user/{handle}')
@KwargsCache(60)
async def v1FetchUser(handle: str) :
	return JsonResponse(
		users.getUser(handle)
	)


@app.get('/v1/fetch_self')
async def v1FetchSelf(req: Request) :
	await req.user.authenticated()

	return JsonResponse(
		users.getSelf(req.user)
	)


@app.post('/v1/update_self')
async def v1UpdateSelf(req: Request, body: UpdateSelf) :
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


@app.get('/v1/all_users')
async def v1FetchUsers(req: Request) :
	await req.user.verify_scope(Scope.admin)
	return JsonResponse(
		users.getUsers()
	)


@app.post('/v1/set_mod')
async def v1SetMod(req: Request, body: SetMod) :
	await req.user.verify_scope(Scope.admin)
	users.setMod(body.handle, body.mod)
	return NoContentResponse


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='0.0.0.0', port=5005)
