from api.routers.auth_route import auth_router
from api.routers.users import user_router
from api.routers.batch_route import batch_router


def initialize_routes(app):
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(batch_router)