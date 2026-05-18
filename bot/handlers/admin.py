import random

from vkbottle.bot import BotLabeler, Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadRule, StateRule

from bot.config import settings
from bot.database.crud.reports import create_report, get_unreviewed_reports, mark_reviewed
from bot.database.crud.users import ban_user, get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.keyboards.main_menu import back_kb
from bot.keyboards.search import incoming_request_kb
from bot.states.search_states import ReportState

labeler = BotLabeler()


def _report_kb(report_id: int, reported_user_id: int) -> str:
    from vkbottle import Callback, Keyboard, KeyboardButtonColor
    kb = Keyboard(inline=True)
    kb.add(
        Callback("🔨 Забанить", {"a": "adm_ban", "uid": reported_user_id, "rid": report_id}),
        color=KeyboardButtonColor.NEGATIVE,
    )
    kb.add(
        Callback("✅ Закрыть", {"a": "adm_close", "rid": report_id}),
        color=KeyboardButtonColor.POSITIVE,
    )
    return kb.get_json()


# ─── Жалобы ──────────────────────────────────────────────────────────────────

@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "report"}))
async def start_report(event: MessageEvent) -> None:
    entity_id = event.object.payload["id"]
    peer_id = event.object.peer_id

    # Сохраняем ID жалуемого в state через отдельное сообщение боту
    await event.show_snackbar("Напишите боту причину жалобы")
    await event.ctx_api.messages.send(
        peer_id=peer_id,
        message="🚩 Опишите причину жалобы одним сообщением:",
        random_id=random.randint(0, 2**30),
    )
    # Примечание: state устанавливается через отдельный механизм — здесь сохраняем через API
    # В реальном проекте используем Redis или хранилище для peer_id → reported_id
    # Упрощённо: просим написать "жалоба на ID <number>"
    await event.ctx_api.messages.send(
        peer_id=peer_id,
        message=f"(Для автоматической обработки укажите: жалоба {entity_id})",
        random_id=random.randint(0, 2**30),
    )


@labeler.message(text=lambda t: t and t.lower().startswith("жалоба"))
async def submit_report(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: жалоба <ID> [причина]")
        return

    try:
        entity_id = int(parts[1])
    except ValueError:
        await message.answer("Формат: жалоба <ID> [причина]")
        return

    reason = " ".join(parts[2:]) if len(parts) > 2 else "Не указана"

    async with AsyncSessionLocal() as session:
        reporter = await get_user_by_tg_id(session, message.from_id)
        if not reporter:
            return
        await create_report(session, reporter_id=reporter.id, reported_id=entity_id, reason=reason)

    await message.answer("✅ Жалоба отправлена на модерацию. Спасибо!", keyboard=back_kb())


# ─── Панель администратора ────────────────────────────────────────────────────

@labeler.message(text="/admin")
async def admin_panel(message: Message) -> None:
    if message.from_id not in settings.admin_vk_ids:
        return

    async with AsyncSessionLocal() as session:
        reports = await get_unreviewed_reports(session)

    if not reports:
        await message.answer("✅ Непросмотренных жалоб нет.")
        return

    for report in reports[:10]:
        reporter_vk = report.reporter.tg_id
        reported_vk = report.reported.tg_id
        text = (
            f"🚩 Жалоба #{report.id}\n"
            f"От: VK ID {reporter_vk}\n"
            f"На: VK ID {reported_vk} (внутренний ID: {report.reported.id})\n"
            f"Причина: {report.reason}\n"
            f"Дата: {report.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        await message.answer(text, keyboard=_report_kb(report.id, report.reported.id))


@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "adm_ban"}))
async def admin_ban(event: MessageEvent) -> None:
    if event.object.user_id not in settings.admin_vk_ids:
        await event.show_snackbar("Нет доступа.")
        return
    payload = event.object.payload
    user_id = payload["uid"]
    report_id = payload["rid"]

    async with AsyncSessionLocal() as session:
        await ban_user(session, user_id)
        await mark_reviewed(session, report_id)

    await event.show_snackbar("🔨 Пользователь заблокирован.")


@labeler.raw_event("message_event", MessageEvent, PayloadRule({"a": "adm_close"}))
async def admin_close(event: MessageEvent) -> None:
    if event.object.user_id not in settings.admin_vk_ids:
        await event.show_snackbar("Нет доступа.")
        return
    report_id = event.object.payload["rid"]

    async with AsyncSessionLocal() as session:
        await mark_reviewed(session, report_id)

    await event.show_snackbar("✅ Жалоба закрыта.")
