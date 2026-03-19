import importlib.resources
from fastapi import Request
from fastapi.templating import Jinja2Templates

from insurance_holder.service import DatabaseService


def get_templates() -> Jinja2Templates:
    """
    Get the Jinja2 templates instance for rendering HTML templates.
    :return:
    """
    template_path = importlib.resources.files('insurance_holder.data') / 'templates'
    return Jinja2Templates(directory=str(template_path))


TEMPLATES = get_templates()


def get_db(request: Request) -> DatabaseService:
    return request.app.state.db


async def build_nav_links(request: Request):
    path = request.url.path
    logged_in = request.session.get('logged_in', False)

    if logged_in:
        return []
    else:
        return []
