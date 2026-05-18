from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot.database.crud.startups import create_startup, get_startup_by_captain, update_startup
from bot.database.crud.users import get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.database.models import Startup, StartupStage, UserRole
from bot.keyboards.main_menu import back_kb, confirm_kb, main_menu_kb
from bot.keyboards.registration import (
    STARTUP_NEEDS,
    STARTUP_STAGES,
    startup_needs_kb,
    startup_stage_kb,
)
from bot.states.startup_states import StartupForm
from bot.utils.formatters import fmt_startup
from bot.utils.validators import parse_comma_list, validate_text_length

labeler = BotLabeler()

_STAGE_MAP = {"Идея": "idea", "MVP": "mvp", "Прототип": "prototype", "Масштабирование": "scaling"}


async def start_registration(message: Message) -> None:
    await message.state_peer.set(StartupForm.NAME)
    await message.state_peer.set_data({"tags": [], "needs": []})
    await message.answer("📝 Регистрация стартапа\n\nВведите название стартапа:")


@labeler.message(text="➕ Создать стартап")
async def create_startup_menu(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user:
            return
        existing = await get_startup_by_captain(session, user.id)
        if existing:
            await message.answer(
                f"У вас уже есть стартап:\n\n{fmt_startup(existing)}",
                keyboard=main_menu_kb(user.role),
            )
        else:
            await start_registration(message)


@labeler.message(StateRule(StartupForm.NAME))
async def startup_name(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Название от 2 до 128 символов:")
        return
    d = await message.state_peer.get_data() or {}
    d["name"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StartupForm.DESCRIPTION)
    await message.answer("Опишите стартап:\n(Проблема → Решение)")


@labeler.message(StateRule(StartupForm.DESCRIPTION))
async def startup_description(message: Message) -> None:
    if not validate_text_length(message.text, 20, 1000):
        await message.answer("Описание от 20 до 1000 символов:")
        return
    d = await message.state_peer.get_data() or {}
    d["description"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StartupForm.TAGS)
    await message.answer("Введите теги через запятую:\n(Пример: AI, Медицина, IoT)")


@labeler.message(StateRule(StartupForm.TAGS))
async def startup_tags(message: Message) -> None:
    tags = parse_comma_list(message.text)
    if not tags:
        await message.answer("Введите хотя бы один тег:")
        return
    d = await message.state_peer.get_data() or {}
    d["tags"] = tags
    await message.state_peer.set_data(d)
    await message.state_peer.set(StartupForm.STAGE)
    await message.answer("Выберите стадию стартапа:", keyboard=startup_stage_kb())


@labeler.message(StateRule(StartupForm.STAGE))
async def startup_stage(message: Message) -> None:
    if message.text not in STARTUP_STAGES:
        await message.answer("Выберите из списка:", keyboard=startup_stage_kb())
        return
    d = await message.state_peer.get_data() or {}
    d["stage"] = _STAGE_MAP[message.text]
    await message.state_peer.set_data(d)
    await message.state_peer.set(StartupForm.NEEDS)
    await message.answer(
        "Кто вам нужен? (нажимайте кнопки, затем «➡️ Готово»):",
        keyboard=startup_needs_kb([]),
    )


@labeler.message(StateRule(StartupForm.NEEDS))
async def startup_needs(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    needs: list = d.get("needs", [])

    if message.text == "➡️ Готово":
        if not needs:
            await message.answer("Выберите хотя бы одну роль:", keyboard=startup_needs_kb(needs))
            return
        await message.state_peer.set(StartupForm.CONTACT)
        await message.answer("Введите Telegram-контакт для связи:\n(Пример: @username)")
        return

    if message.text in STARTUP_NEEDS:
        if message.text in needs:
            needs.remove(message.text)
        else:
            needs.append(message.text)
        d["needs"] = needs
        await message.state_peer.set_data(d)

    await message.answer(
        f"Выбрано: {', '.join(needs) or 'ничего'}",
        keyboard=startup_needs_kb(needs),
    )


@labeler.message(StateRule(StartupForm.CONTACT))
async def startup_contact(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректный контакт:")
        return
    d = await message.state_peer.get_data() or {}
    d["contact"] = message.text.strip()
    await message.state_peer.set_data(d)

    preview = Startup(
        captain_id=0, name=d["name"], description=d["description"],
        tags=d.get("tags", []), stage=StartupStage(d["stage"]),
        needs=d.get("needs", []), contact=d["contact"],
    )
    await message.answer(
        f"Проверьте анкету стартапа:\n\n{fmt_startup(preview)}\n\nВсё верно?",
        keyboard=confirm_kb(),
    )


async def save_startup(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    await message.state_peer.delete()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        existing = await get_startup_by_captain(session, user.id)
        if existing:
            await update_startup(session, existing.id, d)
        else:
            await create_startup(session, user.id, d)

    await message.answer("✅ Стартап зарегистрирован!", keyboard=main_menu_kb(UserRole.student))


@labeler.message(text="🚀 Мой стартап")
async def my_startup(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user:
            return
        startup = await get_startup_by_captain(session, user.id)
        if not startup:
            await message.answer("У вас нет стартапа.", keyboard=back_kb())
        else:
            members_text = ""
            if startup.members:
                lines = [f"  • ID{m.user_id} — {m.role_in_team}" for m in startup.members]
                members_text = "\n\n👥 Команда:\n" + "\n".join(lines)
            await message.answer(
                fmt_startup(startup) + members_text,
                keyboard=main_menu_kb(user.role),
            )
