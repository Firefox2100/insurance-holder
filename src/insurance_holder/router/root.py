from fastapi import APIRouter, Depends, Request

from insurance_holder.service import DatabaseService
from insurance_holder.router.utils import get_templates, get_db, build_nav_links

root_router = APIRouter()


@root_router.get('/')
async def get_home(request: Request,
                   db: DatabaseService = Depends(get_db)
                   ):
    nav_links = build_nav_links(request)

    countdown_states = await db.list_countdown_states(
        public=True,
        enabled=True,
    )
