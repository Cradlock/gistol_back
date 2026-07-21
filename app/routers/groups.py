

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.groups import GroupDataSQLAlchemy
from app.models.user import User
from app.models.years import Year
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate
from app.services.groups import GroupService


from app.dependencies import get_current_teacher, get_db, get_group_service

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)





## '/'
# post - create
# get - get by id | get by year
# delete [id] - soft delete 
# patch [id] - update data



@router.get("/",response_model=list[GroupResponse])
async def get_by_year(
    year: Year = Query(... , description="Номер курса от 1 до 6"),
    service: GroupService = Depends(get_group_service)
):
    return await service.get_by_year(year)


@router.post("/",response_model=GroupResponse)
async def create(
    data: GroupCreate,
    admin: User = Depends(get_current_teacher),
    service: GroupService = Depends(get_group_service)
):
    return await service.create_group(data.model_dump())



@router.patch("/{id}", response_model=GroupResponse)
async def partial_update(
    id:int,
    data: GroupUpdate,
    admin: User = Depends(get_current_teacher),
    service: GroupService = Depends(get_group_service)
):
    return await service.partial_update_group(id,data.model_dump())


