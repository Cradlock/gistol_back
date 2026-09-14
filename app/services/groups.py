from app.core.errors import DuplicateError, NotFoundError
from app.core.exceptions import bad_request_exception, conflict_exception, not_found_exception
from app.data.groups import GroupDataSQLAlchemy
from app.models.groups import Group
from app.models.years import Year
from app.schemas import group


class GroupService:
    def __init__(self, repository: GroupDataSQLAlchemy):
        self.repo = repository

    async def create_group(self, data: dict) -> Group:
        try:
            return await self.repo.create(data)
        except DuplicateError:
            raise conflict_exception("That group alrady exists")

    async def get_by_year(self, year: Year) -> group.GroupListResponse:
        groups, total = await self.repo.get_active_by_year(year)
        groups_res = [group.GroupResponse.model_validate(g) for g in groups]
        return group.GroupListResponse(total=total, groups=groups_res)

    async def bulk_soft_delete_group(self, group_ids: group.GroupBulkDeleteRequest) -> int:
        if not group_ids or group_ids.ids.count == 0:
            bad_request_exception("ID list not can be a None")
        return await self.repo.bulk_soft_delete(group_ids.ids)

    async def bulk_return_group(self, group_ids: group.GroupBulkDeleteRequest) -> int:
        if not group_ids or group_ids.ids.count == 0:
            bad_request_exception("ID list not can be a None")
        return await self.repo.bulk_return(group_ids.ids)

    async def partial_update_group(self, id: int, updated_data: dict) -> Group | None:
        existing = await self.repo.get_by_id(id)
        if not existing:
            raise not_found_exception("Group not found")
        try:
            return await self.repo.partial_update(id, updated_data)
        except NotFoundError:
            raise not_found_exception("Group not found")
        except DuplicateError:
            raise conflict_exception("That group alrady exists")

    async def search(self, params: group.GroupSearchParams) -> group.GroupListResponse:
        groups, total = await self.repo.search(params)
        groups_res = [group.GroupResponse.model_validate(g) for g in groups]
        return group.GroupListResponse(total=total, groups=groups_res)
