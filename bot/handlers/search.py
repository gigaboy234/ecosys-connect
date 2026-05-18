import random

from vkbottle.bot import BotLabeler, Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadRule

from bot.database.crud.partners import search_partners
from bot.database.crud.requests import has_pending_request
from bot.database.crud.startups import search_startups
from bot.database.crud.students import search_students
from bot.database.crud.teachers import search_teachers
from bot.database.crud.users import get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.database.models import RequestType
from bot.keyboards.main_menu import back_kb, main_menu_kb
from bot.keyboards.registration import DIRECTIONS, STARTUP_STAGES
from bot.keyboards.search import card_nav_kb, search_filter_kb
from bot.utils.formatters import fmt_partner, fmt_startup, fmt_student, fmt_teacher

labeler = BotLabeler()

PAGE_SIZE = 1  # в VK лучше показывать по одной карточке

_STAGE_MAP = {
    f"Стадия: {s}": v
    for s, v in zip(
        ["Идея", "MVP", "Прототип", "Масштабирование"],
        ["idea", "mvp", "prototype", "scaling"],
    )
}

_SEARCH_TRIGGERS = {
    "🚀 Найти стартап": "startups",
    "👨‍🏫 Найти преподавателя": "teachers",
    "🏭 Найти партнёра": "partners",
    "🎓 Найти студента": "students",
}


@labeler.message(text=list(_SEARCH_TRIGGERS.keys()))
async def start_search(message: Message) -> None:
    entity = _SEARCH_TRIGGERS[message.text]
    await message.state_peer.set_data({"search_entity": entity, "search_page": 0, "search_filter": {}})
    await message.answer(
        f"🔍 Поиск: {message.text}\n\nВыберите фильтр или нажмите «🔍 Все»:",
        keyboard=search_filter_kb(entity),
    )


@labeler.message(text=["🔍 Все"] + list(DIRECTIONS) + [f"Стадия: {s}" for s in ["Идея", "MVP", "Прототип", "Масштабирование"]])
async def apply_filter(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    entity = d.get("search_entity", "startups")
    search_filter: dict = {}

    if message.text != "🔍 Все":
        if message.text in DIRECTIONS:
            search_filter["directions"] = [message.text]
        elif message.text in _STAGE_MAP:
            search_filter["stage"] = _STAGE_MAP[message.text]

    d["search_filter"] = search_filter
    d["search_page"] = 0
    await message.state_peer.set_data(d)
    await _show_card(message, entity, search_filter, 0)


# ─── Callback: навигация ◀️ ▶️ ──────────────────────────────────────────────

@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "prev"}))
async def card_prev(event: MessageEvent) -> None:
    payload = event.object.payload
    entity = payload["e"]
    page = payload["p"]
    await event.show_snackbar("◀️")
    await _show_card_from_event(event, entity, page)


@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "next"}))
async def card_next(event: MessageEvent) -> None:
    payload = event.object.payload
    entity = payload["e"]
    page = payload["p"]
    await event.show_snackbar("▶️")
    await _show_card_from_event(event, entity, page)


@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "noop"}))
async def noop(event: MessageEvent) -> None:
    await event.show_snackbar(".")


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _show_card_from_event(event: MessageEvent, entity: str, page: int) -> None:
    peer_id = event.object.peer_id
    user_vk_id = event.object.user_id

    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, user_vk_id)
        if not user:
            return

        state_data = {}  # нет прямого доступа к state из event в этом контексте
        items, fmt_fn, req_type = await _fetch_items(session, entity, user, {}, page)
        if not items:
            await event.ctx_api.messages.send(
                peer_id=peer_id, message="😔 Больше нет анкет.", random_id=random.randint(0, 2**30)
            )
            return

        item = items[0]
        already_sent = await has_pending_request(
            session, from_user_id=user.id, request_type=req_type,
            startup_id=item.id if entity == "startups" else None,
            to_user_id=item.id if entity != "startups" else None,
        )
        kb = card_nav_kb(entity, page, page + 2, item.id, req_type.value, already_sent)
        await event.ctx_api.messages.send(
            peer_id=peer_id, message=fmt_fn(item), keyboard=kb, random_id=random.randint(0, 2**30)
        )


async def _show_card(message: Message, entity: str, search_filter: dict, page: int) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user:
            return

        items, fmt_fn, req_type = await _fetch_items(session, entity, user, search_filter, page)
        if not items:
            await message.answer("😔 По вашему запросу никого не найдено.", keyboard=back_kb())
            return

        item = items[0]
        already_sent = await has_pending_request(
            session, from_user_id=user.id, request_type=req_type,
            startup_id=item.id if entity == "startups" else None,
            to_user_id=item.id if entity != "startups" else None,
        )
        kb = card_nav_kb(entity, page, page + 2, item.id, req_type.value, already_sent)
        await message.answer(fmt_fn(item), keyboard=kb)


async def _fetch_items(session, entity: str, user, search_filter: dict, page: int):
    offset = page * PAGE_SIZE
    limit = PAGE_SIZE + 1

    if entity == "startups":
        items = await search_startups(
            session, exclude_captain_id=user.id, offset=offset, limit=limit, **search_filter
        )
        return items[:PAGE_SIZE], fmt_startup, RequestType.join_startup

    if entity == "teachers":
        items = await search_teachers(session, offset=offset, limit=limit, **search_filter)
        return items[:PAGE_SIZE], fmt_teacher, RequestType.consult_student

    if entity == "students":
        items = await search_students(
            session, exclude_user_id=user.id, offset=offset, limit=limit, **search_filter
        )
        return items[:PAGE_SIZE], fmt_student, RequestType.intern_search

    if entity == "partners":
        items = await search_partners(session, offset=offset, limit=limit)
        return items[:PAGE_SIZE], fmt_partner, RequestType.partner_startup

    return [], None, None
