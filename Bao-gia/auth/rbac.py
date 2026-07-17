"""
RBAC middleware — chặn ở TẦNG SERVICE, không chỉ ẩn nút trên UI.
Dùng require_role() bên trong mọi hàm service nhạy cảm (duyệt báo giá,
xóa dữ liệu, gửi email...) để đảm bảo dù người dùng có "bypass" UI
(gọi thẳng qua console/API) vẫn không thực hiện được hành vi vượt quyền.
"""
from models.models import RoleEnum


class PermissionDenied(Exception):
    pass


ROLE_HIERARCHY_ACTIONS = {
    # action_key: các role được phép thực hiện
    "approve_manager_step": {RoleEnum.SALES_MANAGER, RoleEnum.ADMIN},
    "approve_director_step": {RoleEnum.SALES_DIRECTOR, RoleEnum.CEO, RoleEnum.ADMIN},
    "create_quotation": {RoleEnum.SALESMAN, RoleEnum.SALES_MANAGER,
                          RoleEnum.SALES_DIRECTOR, RoleEnum.CEO, RoleEnum.ADMIN},
    "send_email": {RoleEnum.SALESMAN, RoleEnum.SALES_MANAGER,
                   RoleEnum.SALES_DIRECTOR, RoleEnum.CEO, RoleEnum.ADMIN},
    "manage_products": {RoleEnum.ADMIN, RoleEnum.SALES_DIRECTOR, RoleEnum.CEO},
    "view_all_dashboard": {RoleEnum.CEO, RoleEnum.SALES_DIRECTOR, RoleEnum.ADMIN},
}


def require_role(current_role: RoleEnum, action_key: str):
    """Raise PermissionDenied nếu role hiện tại không được phép thực hiện action_key."""
    allowed = ROLE_HIERARCHY_ACTIONS.get(action_key)
    if allowed is None:
        raise ValueError(f"Action key '{action_key}' chưa được khai báo trong RBAC.")
    if current_role not in allowed:
        raise PermissionDenied(
            f"Vai trò '{current_role.value}' không có quyền thực hiện hành động '{action_key}'."
        )
    return True


def has_permission(current_role: RoleEnum, action_key: str) -> bool:
    """Kiểm tra quyền không raise exception — dùng để ẩn/hiện UI."""
    try:
        return require_role(current_role, action_key)
    except PermissionDenied:
        return False
