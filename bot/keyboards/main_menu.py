from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import UserRole


def role_selection_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎓 Студент", callback_data="role:student"))
    builder.row(InlineKeyboardButton(text="🚀 Стартап", callback_data="role:startup"))
    builder.row(InlineKeyboardButton(text="👨‍🏫 Преподаватель", callback_data="role:teacher"))
    builder.row(InlineKeyboardButton(text="🏭 Индустриальный партнёр", callback_data="role:partner"))
    return builder.as_markup()


def main_menu_kb(role: UserRole) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if role == UserRole.student:
        builder.row(InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu:profile"))
        builder.row(InlineKeyboardButton(text="🚀 Найти стартап", callback_data="menu:search_startups"))
        builder.row(InlineKeyboardButton(text="👨‍🏫 Найти преподавателя", callback_data="menu:search_teachers"))
        builder.row(InlineKeyboardButton(text="➕ Создать стартап", callback_data="menu:create_startup"))
        builder.row(InlineKeyboardButton(text="📬 Входящие заявки", callback_data="menu:incoming"))

    elif role == UserRole.startup:
        builder.row(InlineKeyboardButton(text="🚀 Мой стартап", callback_data="menu:my_startup"))
        builder.row(InlineKeyboardButton(text="👥 Управление командой", callback_data="menu:team"))
        builder.row(InlineKeyboardButton(text="👨‍🏫 Найти наставника", callback_data="menu:search_teachers"))
        builder.row(InlineKeyboardButton(text="🏭 Найти партнёра", callback_data="menu:search_partners"))
        builder.row(InlineKeyboardButton(text="📬 Входящие заявки", callback_data="menu:incoming"))

    elif role == UserRole.teacher:
        builder.row(InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu:profile"))
        builder.row(InlineKeyboardButton(text="🚀 Найти стартап", callback_data="menu:search_startups"))
        builder.row(InlineKeyboardButton(text="🎓 Найти студента", callback_data="menu:search_students"))
        builder.row(InlineKeyboardButton(text="📬 Входящие заявки", callback_data="menu:incoming"))

    elif role == UserRole.partner:
        builder.row(InlineKeyboardButton(text="🏭 Мой профиль", callback_data="menu:profile"))
        builder.row(InlineKeyboardButton(text="🚀 Найти стартап", callback_data="menu:search_startups"))
        builder.row(InlineKeyboardButton(text="🎓 Найти студента", callback_data="menu:search_students"))
        builder.row(InlineKeyboardButton(text="📬 Входящие заявки", callback_data="menu:incoming"))

    builder.row(InlineKeyboardButton(text="🔄 Сменить роль", callback_data="menu:change_role"))
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")]
    ])


def confirm_kb(confirm_data: str, cancel_data: str = "menu:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data),
        ]
    ])


def yes_no_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=yes_data),
            InlineKeyboardButton(text="❌ Нет", callback_data=no_data),
        ]
    ])
