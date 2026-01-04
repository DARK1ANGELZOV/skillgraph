from enum import Enum


class Role(str, Enum):
    USER = "user"                # Кандидат
    HR = "hr"                    # HR / рекрутер
    SUPERVISOR = "supervisor"    # Руководитель / нанимающий менеджер
    ADMIN = "admin"              # Администратор компании
    SUPERADMIN = "superadmin"    # Системный администратор (создатели платформы)
