from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.startups import (
    create_startup,
    get_startup_by_captain,
    get_startup_by_id,
    update_startup,
)
from bot.database.crud.users import get_user_by_tg_id
from bot.keyboards.main_menu import back_to_menu_kb, confirm_kb
from bot.keyboards.registration import startup_needs_kb, startup_stage_kb
from bot.states.startup_states import StartupForm
from bot.utils.formatters import fmt_startup
from bot.utils.validators import validate_text_length

router = Router()

_STAGE_MAP = {
    "Идея": "idea",
    "MVP": "mvp",
    "Прототип": "prototype",
    "Масштабирование": "scaling",
}


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(StartupForm.name)
    await state.update_data(tags=[], needs=[])
    await message.answer(
        "📝 <b>Регистрация стартапа</b>\n\nВведите <b>название</b> вашего стартапа:",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:create_startup")
async def create_startup_menu(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)
    existing = await get_startup_by_captain(session, user.id)
    if existing:
        await callback.message.edit_text(
            f"У вас уже есть стартап: <b>{existing.name}</b>\n\n{fmt_startup(existing)}",
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            "Начинаем регистрацию стартапа...", parse_mode="HTML"
        )
        await start_registration(callback.message, state)
    await callback.answer()


@router.message(StartupForm.name)
async def startup_name(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Название должно быть от 2 до 128 символов:")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(StartupForm.description)
    await message.answer(
        "Опишите ваш стартап:\n<i>Формат: Проблема → Решение</i>",
        parse_mode="HTML",
    )


@router.message(StartupForm.description)
async def startup_description(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 20, 1000):
        await message.answer("Описание должно быть от 20 до 1000 символов:")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(StartupForm.tags)
    await message.answer(
        "Введите <b>теги</b> (технологическое направление) через запятую:\n"
        "<i>Пример: AI, Медицина, IoT</i>",
        parse_mode="HTML",
    )


@router.message(StartupForm.tags)
async def startup_tags(message: Message, state: FSMContext) -> None:
    from bot.utils.validators import parse_comma_list
    tags = parse_comma_list(message.text)
    if not tags:
        await message.answer("Введите хотя бы один тег:")
        return
    await state.update_data(tags=tags)
    await state.set_state(StartupForm.stage)
    await message.answer(
        "Выберите <b>стадию</b> вашего стартапа:",
        reply_markup=startup_stage_kb(),
        parse_mode="HTML",
    )


@router.callback_query(StartupForm.stage, F.data.startswith("stage:"))
async def startup_stage(callback: CallbackQuery, state: FSMContext) -> None:
    stage_label = callback.data.split(":", 1)[1]
    stage_value = _STAGE_MAP.get(stage_label, "idea")
    await state.update_data(stage=stage_value)
    await state.set_state(StartupForm.needs)
    await callback.message.edit_text(
        "Выберите, <b>кто вам нужен</b> в команду (можно несколько):",
        reply_markup=startup_needs_kb([]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(StartupForm.needs, F.data.startswith("need:"))
async def startup_needs_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    if value == "done":
        data = await state.get_data()
        if not data.get("needs"):
            await callback.answer("Выберите хотя бы одну роль!", show_alert=True)
            return
        await state.set_state(StartupForm.contact)
        await callback.message.edit_text(
            "Введите контактный <b>Telegram</b> для связи\n<i>Пример: @username</i>",
            parse_mode="HTML",
        )
    else:
        data = await state.get_data()
        needs = data.get("needs", [])
        if value in needs:
            needs.remove(value)
        else:
            needs.append(value)
        await state.update_data(needs=needs)
        await callback.message.edit_reply_markup(reply_markup=startup_needs_kb(needs))
    await callback.answer()


@router.message(StartupForm.contact)
async def startup_contact(message: Message, state: FSMContext) -> None:
    contact = message.text.strip()
    if not validate_text_length(contact, 2, 128):
        await message.answer("Введите корректный контакт:")
        return
    await state.update_data(contact=contact)
    await state.set_state(StartupForm.confirm)

    data = await state.get_data()
    from bot.database.models import Startup, StartupStage

    preview = Startup(
        captain_id=0,
        name=data["name"],
        description=data["description"],
        tags=data.get("tags", []),
        stage=StartupStage(data["stage"]),
        needs=data.get("needs", []),
        contact=data["contact"],
    )

    await message.answer(
        f"<b>Проверьте анкету стартапа:</b>\n\n{fmt_startup(preview)}\n\nВсё верно?",
        reply_markup=confirm_kb("startup:save", "menu:main"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "startup:save")
async def startup_save(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    user = await get_user_by_tg_id(session, callback.from_user.id)
    existing = await get_startup_by_captain(session, user.id)

    if existing:
        await update_startup(session, existing.id, data)
    else:
        await create_startup(session, user.id, data)

    from bot.keyboards.main_menu import main_menu_kb
    from bot.database.models import UserRole

    await callback.message.edit_text(
        "✅ <b>Стартап зарегистрирован!</b>",
        reply_markup=main_menu_kb(UserRole.student),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:my_startup")
async def my_startup(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)
    startup = await get_startup_by_captain(session, user.id)
    if not startup:
        await callback.message.edit_text(
            "У вас нет зарегистрированного стартапа.",
            reply_markup=back_to_menu_kb(),
        )
    else:
        members_text = ""
        if startup.members:
            lines = [f"  • {m.user.username or 'User'} — {m.role_in_team}" for m in startup.members]
            members_text = "\n👥 <b>Команда:</b>\n" + "\n".join(lines)

        await callback.message.edit_text(
            fmt_startup(startup) + members_text,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
    await callback.answer()
