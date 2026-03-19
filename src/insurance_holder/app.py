import uvicorn
from fastapi import FastAPI

from insurance_holder.router import countdown_router, root_router


def create_app():
    app = FastAPI(
        title='Insurance Holder API',
        description='API for managing insurance holders and their associated data.',
        version='1.0.0',
    )

    app.include_router(root_router)
    app.include_router(countdown_router)

    return app


if __name__ == '__main__':
    app = create_app()

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
    )
