import secrets
from contextlib import asynccontextmanager
import uvicorn
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from databases import Database

from insurance_holder import __version__ as insurance_holder_version
from insurance_holder.etc.consts import CONFIG, STATIC_FILE_PATH, LOGGER
from insurance_holder.service.database import DatabaseService
from insurance_holder.router import countdown_router, root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    :param app: The FastAPI application instance.
    """
    LOGGER.debug('System configuration loaded: %s', CONFIG.model_dump_json())

    client = Database(CONFIG.database_url)
    await client.connect()

    app.state.db = DatabaseService(client)

    try:
        yield
    except Exception as e:
        LOGGER.critical('Fatal error during application lifespan: %s', str(e), exc_info=True)
        raise e
    finally:
        pass


def create_app():
    app = FastAPI(
        title='Insurance Holder',
        description='A service working as an insurance policy against involuntary disappearance.',
        version=insurance_holder_version,
        license_info={
            'name': 'GNU General Public License v3.0',
            'url': 'https://github.com/Firefox2100/insurance-holder/blob/main/LICENSE',
        },
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=(),
        allow_credentials=True,
        allow_methods=('GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'),
        allow_headers=(
            'Authorization',
            'Content-Type',
            'Accept',
            'X-Requested-With',
            'X-CSRF-Token',
        ),
    )

    @app.middleware('http')
    async def disable_cors_for_api(request, call_next):
        if request.url.path.startswith('/api'):
            request.scope['cors_exempt'] = True

        response = await call_next(request)

        if request.url.path.startswith('/api'):
            response.headers['Access-Control-Allow-Origin'] = '*'

        return response

    @app.middleware('http')
    async def csp_headers(request, call_next):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        if any([
            request.url.path.startswith('/static/'),
            request.url.path.startswith('/api/'),
            request.url.path.startswith('/docs'),
            request.url.path.startswith('/redoc'),
        ]):
            return response

        policy = "; ".join([
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'self'",
            "form-action 'self'",
            "img-src 'self' data:",
            "font-src 'self'",
            "style-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",
        ])
        if CONFIG.use_https or request.url.scheme == 'https':
            policy += "; upgrade-insecure-requests"

        response.headers['Content-Security-Policy'] = policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response

    app.add_middleware(
        SessionMiddleware,
        secret_key=CONFIG.secret_key,
        same_site='lax',
        https_only=CONFIG.use_https,
    )

    app.include_router(root_router)
    app.include_router(countdown_router)

    app.mount('/static', StaticFiles(directory=str(STATIC_FILE_PATH)), name='static')

    return app


if __name__ == '__main__':
    app = create_app()

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
    )
