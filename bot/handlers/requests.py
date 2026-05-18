import random

from vkbottle.bot import BotLabeler, Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadRule

from bot.database.crud.requests import (
    create_request,
    get_pending_for_startup,
    get_pending_for_user,
    get_request_by_id,
    has_pending_request,
    set_request_status,
)
from bot.database.crud.startups import add_member, get_startup_by_captain
from bot.database.crud.users import get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.database.models import RequestStatus, RequestType, UserRole
from bot.keyboards.main_menu import back_kb, main_menu_kb
from bot.keyboards.search import incoming_request_kb

labeler = BotLabeler()

_REQ_LABELS = {
    RequestType.join_startup: "Вступление в стартап",
    RequestType.mentor_startup: "Наставничество",
    RequestType.consult_student: "Консультация",
    RequestType.partner_startup: "Партнёрство",
    RequestType.intern_search: "Стажировка",
}


# ─── Отправка заявки (callback с карточки) ───────────────────────────────────

@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "apply"}))
async def send_application(event: MessageEvent) -> None:
    payload = event.object.payload
    req_type = RequestType(payload["rt"])
    entity_id = payload["id"]
    user_vk_id = event.object.user_id

    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, user_vk_id)
        if not user:
            await event.show_snackbar("Ошибка: профиль не найден.")
            return

        startup_id = entity_id if req_type == RequestType.join_startup else None
        to_user_id = entity_id if req_type != RequestType.join_startup else None

        already = await has_pending_request(
            session, from_user_id=user.id, request_type=req_type,
            startup_id=startup_id, to_user_id=to_user_id,
        )
        if already:
            await event.show_snackbar("⏳ Вы уже отправили заявку!")
            return

        await create_request(session, from_user_id=user.id, request_type=req_type,
                             startup_id=startup_id, to_user_id=to_user_id)

    await event.show_snackbar("✅ Заявка отправлена!")


# ─── Входящие заявки ─────────────────────────────────────────────────────────

@labeler.message(text="📬 Входящие заявки")
async def show_incoming(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user:
            return

        reqs = []
        if user.role == UserRole.student:
            startup = await get_startup_by_captain(session, user.id)
            if startup:
                reqs = await get_pending_for_startup(session, startup.id)
        else:
            reqs = await get_pending_for_user(session, user.id)

        if not reqs:
            await message.answer("📭 Входящих заявок нет.", keyboard=main_menu_kb(user.role))
            return

        for req in reqs[:5]:
            sender = req.from_user
            sender_name = f"VK ID {sender.tg_id}"
            text = (
                f"📬 Заявка #{req.id}\n"
                f"От: {sender_name}\n"
                f"Тип: {_REQ_LABELS.get(req.request_type, str(req.request_type))}"
            )
            await message.answer(text, keyboard=incoming_request_kb(req.id))


# ─── Принять / Отклонить (callback) ──────────────────────────────────────────

@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "req_accept"}))
async def accept_request(event: MessageEvent) -> None:
    request_id = event.object.payload["id"]
    user_vk_id = event.object.user_id

    async with AsyncSessionLocal() as session:
        req = await set_request_status(session, request_id, RequestStatus.accepted)
        if not req:
            await event.show_snackbar("Заявка не найдена.")
            return

        if req.request_type == RequestType.join_startup and req.startup_id:
            await add_member(session, req.startup_id, req.from_user_id, "Участник")

        sender_vk_id = req.from_user.tg_id

    await event.show_snackbar("✅ Заявка принята!")

    # Уведомляем отправителя
    try:
        await event.ctx_api.messages.send(
            user_id=sender_vk_id,
            message="🎉 Ваша заявка принята!\n\nСвяжитесь с командой напрямую в ВКонтакте.",
            random_id=random.randint(0, 2**30),
        )
    except Exception:
        pass


@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "req_reject"}))
async def reject_request(event: MessageEvent) -> None:
    request_id = event.object.payload["id"]

    async with AsyncSessionLocal() as session:
        req = await set_request_status(session, request_id, RequestStatus.rejected)
        if not req:
            await event.show_snackbar("Заявка не найдена.")
            return
        sender_vk_id = req.from_user.tg_id

    await event.show_snackbar("Заявка отклонена.")

    try:
        await event.ctx_api.messages.send(
            user_id=sender_vk_id,
            message="😔 Ваша заявка была отклонена. Не расстраивайтесь — попробуйте другие варианты!",
            random_id=random.randint(0, 2**30),
        )
    except Exception:
        pass
