


from app.core.errors import DuplicateError
from app.core.exceptions import bad_request_exception, conflict_exception, not_found_exception
from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence

from app.models.groups import Group
from app.models.years import Year
from app.schemas import group


class GroupDataAsbtract(ABC):
    
    #=== Read 
    @abstractmethod
    async def get_by_id(self,id: int) -> Group | None:
        pass 
    
    @abstractmethod
    async def get_active_by_year(self, year:Year) -> tuple[list[Group],int]:
        pass

    @abstractmethod
    async def search(self,params: group.GroupSearchParams) -> tuple[list[Group],int]:
        pass
    #=== Update
    @abstractmethod
    async def partial_update(self, id:int,update_data:dict) -> Optional[Group]:
        pass 


    #=== Create 
    @abstractmethod
    async def create(self,data: dict) -> Group:
        pass 


class GroupService:
    def __init__(self, repository: GroupDataAsbtract):
        if repository is None:
            raise ValueError("GroupService требует валидный repository")
        self.repo = repository
       
    async def create_group(self, data: dict) -> Group:
        
        try:
            result = await self.repo.create(data)
            
            return result;
        except DuplicateError:
            raise conflict_exception("That group alrady exists")

    
    async def get_by_year(self,year: Year) -> group.GroupListResponse:
        groups,total = await self.repo.get_active_by_year(year)
            
        groups_res = [group.GroupResponse.model_validate(g) for g in groups]
        
        return group.GroupListResponse(
            total=total,
            groups=groups_res
        )
        
    async def soft_delete_group(self, group_id: int) -> None:
        group = await self.repo.get_by_id(group_id)
        if not group:
            raise not_found_exception("Group not found")
            
        await self.repo.partial_update(group_id, {"is_active": False})
     

    async def partial_update_group(self,id:int, updated_data:dict) -> Group | None:
        group = await self.repo.get_by_id(id)
        if not group:
            raise not_found_exception("Group not found")
        
        return await self.repo.partial_update(id,updated_data) 
        

    async def search(self, params: group.GroupSearchParams) -> group.GroupListResponse:
        groups,total = await self.repo.search(params)
            
        groups_res = [group.GroupResponse.model_validate(g) for g in groups]
        
        return group.GroupListResponse(
            total=total,
            groups=groups_res
        ) 

