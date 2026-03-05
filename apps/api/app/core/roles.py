from enum import StrEnum


class CompanyRole(StrEnum):
    OWNER = "OWNER"
    HR_SENIOR = "HR_SENIOR"
    HR_JUNIOR = "HR_JUNIOR"
    SUPERVISOR = "SUPERVISOR"
    SUPERADMIN = "SUPERADMIN"


READONLY_ROLES = {CompanyRole.SUPERVISOR, CompanyRole.OWNER, CompanyRole.HR_SENIOR, CompanyRole.SUPERADMIN}
HR_WRITE_ROLES = {CompanyRole.OWNER, CompanyRole.HR_SENIOR, CompanyRole.HR_JUNIOR, CompanyRole.SUPERADMIN}
OWNER_OR_SUPERADMIN = {CompanyRole.OWNER, CompanyRole.SUPERADMIN}
