from fastapi import APIRouter


root_router = APIRouter()


@root_router.get('/')
async def get_home()
