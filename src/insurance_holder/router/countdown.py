from fastapi import APIRouter, Request, Depends

from insurance_holder.model.countdown import CreateCountdown
from insurance_holder.service import DatabaseService
from insurance_holder.router.utils import get_templates, get_db, build_nav_links


countdown_router = APIRouter(
    prefix='/countdowns',
)


@countdown_router.get('')
async def display_countdowns(request: Request,
                             db: DatabaseService = Depends(get_db)
                             ):
    nav_links = await build_nav_links(request)
    countdown_states = await db.list_countdown_states()

    return get_templates().TemplateResponse(
        'list_countdowns.html',
        {
            'request': request,
            'page_title': 'Countdowns | Insurance Holder',
            'nav_links': nav_links,
            'countdown_states': countdown_states,
        },
    )


@countdown_router.get('/create')
async def create_countdown(request: Request):
    nav_links = await build_nav_links(request)

    return get_templates().TemplateResponse(
        'create_countdown.html',
        {
            'request': request,
            'page_title': 'Create Countdown | Insurance Holder',
            'nav_links': nav_links,
        },
    )


@countdown_router.post('/create')
async def post_create_countdown(countdown: CreateCountdown,
                                db: DatabaseService = Depends(get_db),
                                ):
    countdown_model, first_run = countdown.to_countdown()

    await db.create_countdown(
        countdown=countdown_model,
        first_run=first_run,
    )

    return {
        'ok': True,
        'countdownId': countdown_model.countdown_id,
    }
