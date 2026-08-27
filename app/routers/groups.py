

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.groups import GroupDataSQLAlchemy
from app.models.user import User
from app.models.years import Year
from app.schemas.group import GroupBulkDeleteRequest, GroupCreate, GroupListResponse, GroupResponse, GroupSearchParams, GroupUpdate
from app.services.groups import GroupService


from app.dependencies import get_current_teacher, get_db, get_group_service

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)





## '/'
# post - create
# get - get by id | get by year
# delete [id] - deletes 
# patch [id] - update data



@router.get("/search",response_model=GroupListResponse)
async def search(
    admin: User = Depends(get_current_teacher),
    params: GroupSearchParams = Depends(),
    service: GroupService = Depends(get_group_service)
):
    return await service.search(params) 


@router.get("/",response_model=GroupListResponse)
async def get_by_year(
    year: Year = Query(),
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




@router.delete("/")
async def bulk_delete(
    group_ids: GroupBulkDeleteRequest,
    admin: User = Depends(get_current_teacher),
    service: GroupService = Depends(get_group_service)
): 
    return await service.bulk_soft_delete_group(group_ids) 


@router.patch("/return")
async def bulk_rec(
    group_ids: GroupBulkDeleteRequest,
    admin: User = Depends(get_current_teacher),
    service: GroupService = Depends(get_group_service)
): 
    return await service.bulk_return_group(group_ids) 


