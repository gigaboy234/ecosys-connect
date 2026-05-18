from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.registration import DIRECTIONS, STARTUP_STAGES


def search_filter_kb(entity: str) -> InlineKeyboardMarkup:
    """Показывает фильтры перед поиском: entity = startups | teachers | students | partners"""
    builder = InlineKeyboardBuilder()
    if entity in ("startups", "students"):
        for d in DIRECTIONS:
            builder.row(InlineKeyboardButton(
                text=d, callback_data=f"filter:{entity}:dir:{d}"
            ))
    if entity == "startups":
        for stage in STARTUP_STAGES:
            builder.row(InlineKeyboardButton(
                text=f"Стадия: {stage}", callback_data=f"filter:{entity}:stage:{stage}"
            ))
    builder.row(InlineKeyboardButton(text="🔍 Без фильтра", callback_data=f"filter:{entity}:none"))
    return builder.as_markup()


def card_actions_kb(
    entity: str,
    entity_id: int,
    page: int,
    total: int,
    request_type: str,
    already_sent: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    prev_page = max(0, page - 1)
    next_page = page + 1

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️", callback_data=f"browse:{entity}:{prev_page}"
        ))
    nav_row.append(InlineKeyboardButton(
        text=f"{page + 1}/{total}", callback_data="noop"
    ))
    if page < total - 1:
        nav_row.append(InlineKeyboardButton(
            text="▶️", callback_data=f"browse:{entity}:{next_page}"
        ))
    if nav_row:
        builder.row(*nav_row)

    if already_sent:
        builder.row(InlineKeyboardButton(text="⏳ Заявка уже отправлена", callback_data="noop"))
    else:
        builder.row(InlineKeyboardButton(
            text="📩 Отправить заявку", callback_data=f"apply:{request_type}:{entity_id}"
        ))

    builder.row(InlineKeyboardButton(text="🚩 Пожаловаться", callback_data=f"report:{entity_id}"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"))
    return builder.as_markup()


def incoming_request_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"req:accept:{request_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"req:reject:{request_id}"),
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
    ])
