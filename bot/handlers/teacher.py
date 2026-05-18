from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot.database.crud.teachers import create_teacher, get_teacher_by_user_id, update_teacher
from bot.database.crud.users import get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.database.models import Teacher, TeacherFormat, UserRole
from bot.keyboards.main_menu import back_kb, confirm_kb, main_menu_kb
from bot.keyboards.registration import (
    HELP_TYPES,
    TEACHER_FORMATS,
    help_types_kb,
    teacher_format_kb,
)
from bot.states.teacher_states import TeacherForm
from bot.utils.formatters import fmt_teacher
from bot.utils.validators import parse_comma_list, validate_availability, validate_text_length

labeler = BotLabeler()

_FORMAT_MAP = {"Очно": "offline", "Онлайн": "online", "Смешанно": "mixed"}


async def start_registration(message: Message) -> None:
    await message.state_peer.set(TeacherForm.FULL_NAME)
    await message.state_peer.set_data({"research_directions": [], "competencies": [], "help_types": []})
    await message.answer("📝 Регистрация преподавателя\n\nВведите ваше ФИО:")


@labeler.message(StateRule(TeacherForm.FULL_NAME))
async def teacher_fullname(message: Message) -> None:
    if not validate_text_length(message.text, 5, 128):
        await message.answer("Введите полное ФИО (5–128 символов):")
        return
    d = await message.state_peer.get_data() or {}
    d["full_name"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(TeacherForm.DEGREE)
    await message.answer("Введите учёную степень / должность:")


@labeler.message(StateRule(TeacherForm.DEGREE))
async def teacher_degree(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректную степень/должность:")
        return
    d = await message.state_peer.get_data() or {}
    d["degree"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(TeacherForm.DEPARTMENT)
    await message.answer("Введите кафедру / направление исследований:")


@labeler.message(StateRule(TeacherForm.DEPARTMENT))
async def teacher_department(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректное название кафедры:")
        return
    d = await message.state_peer.get_data() or {}
    d["department"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(TeacherForm.RESEARCH_DIRECTIONS)
    await message.answer("Введите научные направления через запятую:\n(Пример: AI, Биотехнологии)")


@labeler.message(StateRule(TeacherForm.RESEARCH_DIRECTIONS))
async def teacher_directions(message: Message) -> None:
    dirs = parse_comma_list(message.text)
    if not dirs:
        await message.answer("Введите хотя бы одно направление:")
        return
    d = await message.state_peer.get_data() or {}
    d["research_directions"] = dirs
    await message.state_peer.set_data(d)
    await message.state_peer.set(TeacherForm.COMPETENCIES)
    await message.answer("Введите технологические компетенции через запятую:\n(Пример: Python, MATLAB)")


@labeler.message(StateRule(TeacherForm.COMPETENCIES))
async def teacher_competencies(message: Message) -> None:
    comp = parse_comma_list(message.text)
    if not comp:
        await message.answer("Введите хотя бы одну компетенцию:")
        return
    d = await message.state_peer.get_data() or {}
    d["competencies"] = comp
    await message.state_peer.set_data(d)
    await message.state_peer.set(TeacherForm.HELP_TYPES)
    await message.answer(
        "Чем вы можете помочь? (нажимайте кнопки, затем «➡️ Готово»):",
        keyboard=help_types_kb([]),
    )


@labeler.message(StateRule(TeacherForm.HELP_TYPES))
async def teacher_help(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    help_t: list = d.get("help_types", [])

    if message.text == "➡️ Готово":
        if not help_t:
            await message.answer("Выберите хотя бы один тип:", keyboard=help_types_kb(help_t))
            return
        await message.state_peer.set(TeacherForm.AVAILABILITY)
        await message.answer("Введите доступность (часов в неделю, 1–40):")
        return

    if message.text in HELP_TYPES:
        if message.text in help_t:
            help_t.remove(message.text)
        else:
            help_t.append(message.text)
        d["help_types"] = help_t
        await message.state_peer.set_data(d)

    await message.answer(
        f"Выбрано: {', '.join(help_t) or 'ничего'}",
        keyboard=help_types_kb(help_t),
    )


@labeler.message(StateRule(TeacherForm.AVAILABILITY))
async def teacher_availability(message: Message) -> None:
    hours = validate_availability(message.text)
    if hours is None:
        await message.answer("Введите число от 1 до 168:")
        return
    d = await message.state_peer.get_data() or {}
    d["availability"] = hours
    await message.state_peer.set_data(d)
    await message.state_peer.set(TeacherForm.FORMAT)
    await message.answer("Выберите формат участия:", keyboard=teacher_format_kb())


@labeler.message(StateRule(TeacherForm.FORMAT))
async def teacher_format(message: Message) -> None:
    if message.text not in TEACHER_FORMATS:
        await message.answer("Выберите из списка:", keyboard=teacher_format_kb())
        return
    d = await message.state_peer.get_data() or {}
    d["format"] = _FORMAT_MAP[message.text]
    await message.state_peer.set_data(d)

    preview = Teacher(
        user_id=0, full_name=d["full_name"], degree=d["degree"], department=d["department"],
        research_directions=d.get("research_directions", []), competencies=d.get("competencies", []),
        help_types=d.get("help_types", []), availability=d["availability"],
        format=TeacherFormat(d["format"]),
    )
    await message.answer(
        f"Проверьте анкету:\n\n{fmt_teacher(preview)}\n\nВсё верно?",
        keyboard=confirm_kb(),
    )


async def save_teacher(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    await message.state_peer.delete()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        existing = await get_teacher_by_user_id(session, user.id)
        if existing:
            await update_teacher(session, user.id, d)
        else:
            await create_teacher(session, user.id, d)

    await message.answer("✅ Анкета преподавателя сохранена!", keyboard=main_menu_kb(UserRole.teacher))


@labeler.message(text="👤 Мой профиль")
async def show_teacher_profile(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user or user.role != UserRole.teacher:
            return
        profile = await get_teacher_by_user_id(session, user.id)
        if not profile:
            await message.answer("Анкета не найдена.", keyboard=back_kb())
        else:
            await message.answer(fmt_teacher(profile), keyboard=main_menu_kb(UserRole.teacher))
