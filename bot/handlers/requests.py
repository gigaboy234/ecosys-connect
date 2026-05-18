from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.requests import (
    create_request,
    get_pending_for_startup,
    get_pending_for_user,
    get_request_by_id,
    has_pending_request,
    set_request_status,
)
from bot.database.crud.startups import add_member, get_startup_by_captain, get_startup_by_id
from bot.database.crud.users import get_user_by_tg_id
from bot.database.models import RequestStatus, RequestType, UserRole
from bot.keyboards.main_menu import back_to_menu_kb, main_menu_kb
from bot.keyboards.search import incoming_request_kb
from bot.utils.formatters import fmt_startup, fmt_student, fmt_teacher, fmt_partner

router = Router()


@router.callback_query(F.data.startswith("apply:"))
async def send_application(callback: CallbackQuery, session: AsyncSession) -> None:
    # apply:<request_type>:<entity_id>
    parts = callback.data.split(":")
    req_type_str = parts[1]
    entity_id = int(parts[2])

    user = await get_user_by_tg_id(session, callback.from_user.id)
    req_type = RequestType(req_type_str)

    startup_id = entity_id if req_type == RequestType.join_startup else None
    to_user_id = entity_id if req_type != RequestType.join_startup else None

    already = await has_pending_request(
        session,
        from_user_id=user.id,
        request_type=req_type,
        startup_id=startup_id,
        to_user_id=to_user_id,
    )
    if already:
        await callback.answer("Вы уже отправили заявку!", show_alert=True)
        return

    await create_request(
        session,
        from_user_id=user.id,
        request_type=req_type,
        startup_id=startup_id,
        to_user_id=to_user_id,
    )

    await callback.answer("✅ Заявка отправлена!", show_alert=True)


@router.callback_query(F.data == "menu:incoming")
async def show_incoming(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)

    reqs = []
    if user.role == UserRole.student:
        startup = await get_startup_by_captain(session, user.id)
        if startup:
            reqs = await get_pending_for_startup(session, startup.id)
    else:
        reqs = await get_pending_for_user(session, user.id)

    if not reqs:
        await callback.message.edit_text(
            "📭 Входящих заявок нет.", reply_markup=back_to_menu_kb()
        )
        await callback.answer()
        return

    req = reqs[0]
    sender = req.from_user
    sender_info = f"@{sender.username}" if sender.username else f"ID {sender.tg_id}"

    text = (
        f"📬 <b>Входящая заявка</b> ({len(reqs)} шт.)\n\n"
        f"От: {sender_info}\n"
        f"Тип: {_req_type_label(req.request_type)}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=incoming_request_kb(req.id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("req:accept:"))
async def accept_request(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    request_id = int(callback.data.split(":")[2])
    req = await set_request_status(session, request_id, RequestStatus.accepted)
    if not req:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    sender = req.from_user

    if req.request_type == RequestType.join_startup and req.startup_id:
        await add_member(session, req.startup_id, sender.id, "Участник")

    # Уведомляем отправителя
    try:
        await bot.send_message(
            sender.tg_id,
            "🎉 <b>Ваша заявка принята!</b>\n\n"
            "Теперь вы можете связаться с командой напрямую через Telegram.",
            parse_mode="HTML",
        )
    except Exception:
        pass

    user = await get_user_by_tg_id(session, callback.from_user.id)
    await callback.message.edit_text(
        "✅ Заявка принята. Пользователю отправлено уведомление.",
        reply_markup=main_menu_kb(user.role),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("req:reject:"))
async def reject_request(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    request_id = int(callback.data.split(":")[2])
    req = await set_request_status(session, request_id, RequestStatus.rejected)
    if not req:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    sender = req.from_user
    try:
        await bot.send_message(
            sender.tg_id,
            "😔 Ваша заявка была отклонена. Не расстраивайтесь — попробуйте другие варианты!",
        )
    except Exception:
        pass

    user = await get_user_by_tg_id(session, callback.from_user.id)
    await callback.message.edit_text(
        "Заявка отклонена.",
        reply_markup=main_menu_kb(user.role),
    )
    await callback.answer()


def _req_type_label(req_type: RequestType) -> str:
    labels = {
        RequestType.join_startup: "Вступление в стартап",
        RequestType.mentor_startup: "Наставничество для стартапа",
        RequestType.consult_student: "Консультация студента",
        RequestType.partner_startup: "Партнёрство со стартапом",
        RequestType.intern_search: "Стажировка",
    }
    return labels.get(req_type, str(req_type))
