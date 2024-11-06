from api.routers.auth_route import auth_router
from api.routers.users import user_router
from api.routers.batch_route import batch_router
from api.routers.job_post_route import job_post_router


def initialize_routes(app):
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(batch_router)
    app.include_router(job_post_router)