from kh_common.server import Request, ServerApp, UJSONResponse
from kh_common.exceptions.http_error import HttpErrorHandler, NotFound
from kh_common.caching import KwargsCache
from fastapi.responses import Response
from kh_common.models import Scope
from models import UpdateSelf
from users import Users


app = ServerApp(auth_required=False)
users = Users()


@app.on_event('shutdown')
async def shutdown() :
	users.close()


@app.get('/v1/fetch_user/{handle}')
@KwargsCache(60)
async def v1FetchUser(handle: str) :
	return UJSONResponse(
		users.getUser(handle)
	)


@app.get('/v1/fetch_self')
async def v1FetchSelf(req: Request) :
	req.user.authenticated()

	return UJSONResponse(
		users.getSelf(req.user)
	)


@app.post('/v1/update_self')
async def v1UpdateSelf(req: Request, body: UpdateSelf) :
	req.user.authenticated()

	users.updateSelf(
		req.user,
		body.name,
		body.privacy,
		body.icon,
		body.website,
		body.description,
	)

	return Response(None, status_code=204)


@app.get('/v1/all_users')
async def v1FetchUsers(req: Request) :
	req.user.verify_scope(Scope.admin)
	return UJSONResponse(
		users.getUsers()
	)


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='0.0.0.0', port=5005)
