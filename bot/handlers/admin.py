from aiogram import F, Router
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.crud.reports import get_unreviewed_reports, mark_reviewed
from bot.database.crud.users import ban_user, get_user_by_tg_id
from bot.database.crud.reports import create_report
from bot.keyboards.main_menu import back_to_menu_kb
from bot.states.search_states import ReportState
from aiogram.fsm.context import FSMContext

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.admin_ids


# ─── Жалобы ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("report:"))
async def start_report(callback: CallbackQuery, state: FSMContext) -> None:
    reported_id = int(callback.data.split(":")[1])
    await state.set_state(ReportState.reason)
    await state.update_data(reported_entity_id=reported_id)
    await callback.message.answer(
        "🚩 Опишите причину жалобы (коротко):",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()


@router.message(ReportState.reason)
async def submit_report(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    reporter = await get_user_by_tg_id(session, message.from_user.id)
    reported_entity_id = data.get("reported_entity_id", 0)

    await create_report(
        session,
        reporter_id=reporter.id,
        reported_id=reported_entity_id,
        reason=message.text.strip()[:500],
    )

    await message.answer(
        "✅ Жалоба отправлена на модерацию. Спасибо!",
        reply_markup=back_to_menu_kb(),
    )


# ─── Панель администратора ────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "/admin")
async def admin_panel(message: Message, session: AsyncSession) -> None:
    reports = await get_unreviewed_reports(session)
    if not reports:
        await message.answer("✅ Непросмотренных жалоб нет.")
        return

    for report in reports[:10]:
        reporter_name = report.reporter.username or str(report.reporter.tg_id)
        reported_name = report.reported.username or str(report.reported.tg_id)
        text = (
            f"🚩 <b>Жалоба #{report.id}</b>\n"
            f"От: @{reporter_name}\n"
            f"На: @{reported_name} (ID: {report.reported.tg_id})\n"
            f"Причина: {report.reason}\n"
            f"Дата: {report.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔨 Забанить", callback_data=f"admin:ban:{report.reported.id}:{report.id}"
                ),
                InlineKeyboardButton(
                    text="✅ Закрыть", callback_data=f"admin:close:{report.id}"
                ),
            ]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("admin:ban:"))
async def admin_ban(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.admin_ids:
        return
    parts = callback.data.split(":")
    user_id = int(parts[2])
    report_id = int(parts[3])

    await ban_user(session, user_id)
    await mark_reviewed(session, report_id)
    await callback.message.edit_text("🔨 Пользователь заблокирован, жалоба закрыта.")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:close:"))
async def admin_close(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.admin_ids:
        return
    report_id = int(callback.data.split(":")[2])
    await mark_reviewed(session, report_id)
    await callback.message.edit_text("✅ Жалоба закрыта без действий.")
    await callback.answer()
