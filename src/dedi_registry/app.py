import importlib.resources as pkg_resources
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from dedi_registry import __version__ as dedi_registry_version
from dedi_registry.etc.consts import LOGGER, CONFIG
from dedi_registry.database import get_active_db
from dedi_registry.router import api_router, ui_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    :param _: The FastAPI application instance.
    """
    db = get_active_db()

    try:
        LOGGER.info('Starting Decentralised Discovery Network Registry application...')

        await db.init()
        LOGGER.info('Database connection established.')

        LOGGER.info('Application startup complete.')
        yield
    except Exception as e:
        LOGGER.exception('Error during application startup: %s', e)
        raise
    finally:
        LOGGER.info('Stopping Decentralised Discovery Network Registry application...')
        await db.close()

        LOGGER.info('Application shutdown complete.')


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    :return: The configured FastAPI application instance.
    """
    app = FastAPI(
        title='Decentralised Discovery Network Registry',
        version=dedi_registry_version,
        description='A network registry for Decentralised Discovery Gateway systems to '
                    'report the networks for public finding.',
        contact={
            'name': 'Firefox2100',
            'url': 'https://github.com/Firefox2100',
            'email': 'wangyunze16@gmail.com',
        },
        license_info={
            'name': 'GNU GENERAL PUBLIC LICENSE v3.0',
            'url': 'https://github.com/Firefox2100/dedi-registry/blob/main/LICENSE',
        },
        openapi_tags=[
            {
                'name': 'API',
                'description': 'Endpoints for other DDG services to interact with the registry.',
            },
            {
                'name': 'UI',
                'description': 'Endpoints for the web user interface.',
            },
        ],
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=set(CONFIG.allow_origins) or (),
        allow_credentials=True,
        allow_methods=('GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'),
        allow_headers=(
            'Authorization',
            'Content-Type',
            'Accept',
            'X-Requested-With',
        ),
    )

    app.include_router(api_router)
    app.include_router(ui_router)

    static_file_path = pkg_resources.files('dedi_registry.data') / 'static'
    app.mount('/static', StaticFiles(directory=str(static_file_path)), name='static')

    return app


def main():
    """
    Main entry point for the application
    :return:
    """
    app = create_app()

    # Remove the logging handler added in the application code
    # This makes the log propagate to uvicorn's logging configuration
    if LOGGER.hasHandlers():
        for h in LOGGER.handlers[:]:
            LOGGER.removeHandler(h)

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=5000,
        log_config={
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    "()": "uvicorn.logging.DefaultFormatter",
                    'fmt': '[%(asctime)s] [%(process)d] [%(levelname)s]: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S %z',
                },
                'access': {
                    '()': 'uvicorn.logging.AccessFormatter',
                    'fmt': '%(levelprefix)s %(client_addr)s - '
                           '"%(request_line)s" %(status_code)s',
                },
            },
            'handlers': {
                'default': {
                    'formatter': 'default',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stderr',
                },
                'access': {
                    'formatter': 'access',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',
                },
            },
            'loggers': {
                'uvicorn': {
                    'handlers': ['default'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'uvicorn.error': {
                    'handlers': ['default'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'uvicorn.access': {
                    'handlers': ['access'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'root': {
                'handlers': ['default'],
                'level': CONFIG.logging_level.upper(),  # pylint: disable=no-member
            },
        }
    )


if __name__ == '__main__':
    main()
