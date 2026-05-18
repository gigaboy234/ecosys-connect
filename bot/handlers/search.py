from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.requests import has_pending_request
from bot.database.crud.startups import search_startups
from bot.database.crud.students import search_students
from bot.database.crud.teachers import search_teachers
from bot.database.crud.partners import search_partners
from bot.database.crud.users import get_user_by_tg_id
from bot.database.models import RequestType
from bot.keyboards.search import card_actions_kb, search_filter_kb
from bot.utils.formatters import fmt_startup, fmt_student, fmt_teacher, fmt_partner

router = Router()

PAGE_SIZE = 5


# ─── Entry points from main menu ──────────────────────────────────────────────

@router.callback_query(F.data == "menu:search_startups")
async def menu_search_startups(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🔍 <b>Поиск стартапов</b>\n\nВыберите фильтр:",
        reply_markup=search_filter_kb("startups"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:search_teachers")
async def menu_search_teachers(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🔍 <b>Поиск преподавателей</b>\n\nВыберите фильтр:",
        reply_markup=search_filter_kb("teachers"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:search_students")
async def menu_search_students(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🔍 <b>Поиск студентов</b>\n\nВыберите фильтр:",
        reply_markup=search_filter_kb("students"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:search_partners")
async def menu_search_partners(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🔍 <b>Поиск партнёров</b>",
        reply_markup=search_filter_kb("partners"),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Filter selection → show first page ───────────────────────────────────────

@router.callback_query(F.data.startswith("filter:"))
async def apply_filter(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    # filter:<entity>:<type>:<value>  or  filter:<entity>:none
    parts = callback.data.split(":")
    entity = parts[1]
    filter_type = parts[2]
    filter_value = parts[3] if len(parts) > 3 else None

    search_kwargs: dict = {}
    if filter_type == "dir" and filter_value:
        search_kwargs["directions"] = [filter_value]
    elif filter_type == "stage" and filter_value:
        from bot.database.models import StartupStage
        _stage_map = {"Идея": "idea", "MVP": "mvp", "Прототип": "prototype", "Масштабирование": "scaling"}
        search_kwargs["stage"] = _stage_map.get(filter_value, filter_value)

    await state.update_data(search_entity=entity, search_kwargs=search_kwargs, search_page=0)
    await _show_page(callback, session, entity, search_kwargs, 0)
    await callback.answer()


# ─── Pagination ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("browse:"))
async def browse_page(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    _, entity, page_str = callback.data.split(":")
    page = int(page_str)
    data = await state.get_data()
    search_kwargs = data.get("search_kwargs", {})
    await _show_page(callback, session, entity, search_kwargs, page)
    await callback.answer()


async def _show_page(
    callback: CallbackQuery,
    session: AsyncSession,
    entity: str,
    search_kwargs: dict,
    page: int,
) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)

    if entity == "startups":
        items = await search_startups(
            session, exclude_captain_id=user.id, offset=page * PAGE_SIZE, limit=PAGE_SIZE + 1, **search_kwargs
        )
        fmt = fmt_startup
        req_type = RequestType.join_startup
    elif entity == "teachers":
        items = await search_teachers(
            session, offset=page * PAGE_SIZE, limit=PAGE_SIZE + 1, **search_kwargs
        )
        fmt = fmt_teacher
        req_type = RequestType.consult_student
    elif entity == "students":
        items = await search_students(
            session, exclude_user_id=user.id, offset=page * PAGE_SIZE, limit=PAGE_SIZE + 1, **search_kwargs
        )
        fmt = fmt_student
        req_type = RequestType.intern_search
    elif entity == "partners":
        items = await search_partners(
            session, offset=page * PAGE_SIZE, limit=PAGE_SIZE + 1, **search_kwargs
        )
        fmt = fmt_partner
        req_type = RequestType.partner_startup
    else:
        return

    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]

    if not items:
        from bot.keyboards.main_menu import back_to_menu_kb
        await callback.message.edit_text(
            "😔 По вашему запросу никого не найдено.",
            reply_markup=back_to_menu_kb(),
        )
        return

    item = items[0]
    entity_id = item.id

    # Определяем, отправлена ли уже заявка
    already_sent = await has_pending_request(
        session,
        from_user_id=user.id,
        request_type=req_type,
        startup_id=entity_id if entity == "startups" else None,
        to_user_id=entity_id if entity != "startups" else None,
    )

    total_on_page = len(items)
    kb = card_actions_kb(
        entity=entity,
        entity_id=entity_id,
        page=page,
        total=page + (2 if has_next else 1),
        request_type=req_type.value,
        already_sent=already_sent,
    )

    await callback.message.edit_text(
        fmt(item),
        reply_markup=kb,
        parse_mode="HTML",
    )
