from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot.database.crud.students import create_student, get_student_by_user_id, update_student
from bot.database.crud.users import get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.database.models import StudentGoal, UserRole
from bot.keyboards.main_menu import back_kb, confirm_kb, main_menu_kb
from bot.keyboards.registration import (
    DIRECTIONS,
    STUDENT_GOALS,
    TECH_INTERESTS,
    directions_kb,
    skip_kb,
    student_goal_kb,
    tech_interests_kb,
)
from bot.states.student_states import StudentForm
from bot.utils.formatters import fmt_student
from bot.utils.validators import parse_comma_list, validate_text_length, validate_url, validate_year

labeler = BotLabeler()

_GOAL_MAP = {
    "Ищу стартап": "find_startup",
    "Хочу создать стартап": "create_startup",
    "Хочу найти преподавателя": "find_teacher",
}


async def start_registration(message: Message) -> None:
    await message.state_peer.set(StudentForm.NAME)
    await message.state_peer.set_data({"directions": [], "tech_interests": []})
    await message.answer("📝 Регистрация студента\n\nВведите ваше имя:")


@labeler.message(StateRule(StudentForm.NAME))
async def student_name(message: Message) -> None:
    if not validate_text_length(message.text, 2, 50):
        await message.answer("Имя должно быть от 2 до 50 символов:")
        return
    d = await message.state_peer.get_data() or {}
    d["name"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.SURNAME)
    await message.answer("Введите вашу фамилию:")


@labeler.message(StateRule(StudentForm.SURNAME))
async def student_surname(message: Message) -> None:
    if not validate_text_length(message.text, 2, 50):
        await message.answer("Фамилия от 2 до 50 символов:")
        return
    d = await message.state_peer.get_data() or {}
    d["surname"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.UNIVERSITY)
    await message.answer("Введите название учебного заведения:")


@labeler.message(StateRule(StudentForm.UNIVERSITY))
async def student_university(message: Message) -> None:
    if not validate_text_length(message.text, 3, 128):
        await message.answer("Введите корректное название:")
        return
    d = await message.state_peer.get_data() or {}
    d["university"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.YEAR)
    await message.answer("Введите ваш курс (1–6):")


@labeler.message(StateRule(StudentForm.YEAR))
async def student_year(message: Message) -> None:
    year = validate_year(message.text)
    if year is None:
        await message.answer("Курс — число от 1 до 6:")
        return
    d = await message.state_peer.get_data() or {}
    d["year"] = year
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.FACULTY)
    await message.answer("Введите факультет / кафедру:")


@labeler.message(StateRule(StudentForm.FACULTY))
async def student_faculty(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректное название:")
        return
    d = await message.state_peer.get_data() or {}
    d["faculty"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.DIRECTIONS)
    await message.answer(
        "Выберите направления (нажимайте кнопки, затем «➡️ Готово»):",
        keyboard=directions_kb(d.get("directions", [])),
    )


@labeler.message(StateRule(StudentForm.DIRECTIONS))
async def student_directions(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    dirs: list = d.get("directions", [])

    if message.text == "➡️ Готово":
        if not dirs:
            await message.answer("Выберите хотя бы одно направление:", keyboard=directions_kb(dirs))
            return
        await message.state_peer.set(StudentForm.TECH_INTERESTS)
        await message.state_peer.set_data({**d, "tech_interests": []})
        await message.answer(
            "Выберите технологические интересы:",
            keyboard=tech_interests_kb([]),
        )
        return

    if message.text in DIRECTIONS:
        if message.text in dirs:
            dirs.remove(message.text)
        else:
            dirs.append(message.text)
        d["directions"] = dirs
        await message.state_peer.set_data(d)

    await message.answer(
        f"Выбрано: {', '.join(dirs) or 'ничего'}\nПродолжайте выбирать или нажмите «➡️ Готово»:",
        keyboard=directions_kb(dirs),
    )


@labeler.message(StateRule(StudentForm.TECH_INTERESTS))
async def student_tech(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    tech: list = d.get("tech_interests", [])

    if message.text == "➡️ Готово":
        await message.state_peer.set(StudentForm.SKILLS)
        await message.answer("Введите навыки через запятую:\n(Пример: Python, SQL, Figma)")
        return

    if message.text in TECH_INTERESTS:
        if message.text in tech:
            tech.remove(message.text)
        else:
            tech.append(message.text)
        d["tech_interests"] = tech
        await message.state_peer.set_data(d)

    await message.answer(
        f"Выбрано: {', '.join(tech) or 'ничего'}",
        keyboard=tech_interests_kb(tech),
    )


@labeler.message(StateRule(StudentForm.SKILLS))
async def student_skills(message: Message) -> None:
    skills = parse_comma_list(message.text)
    if not skills:
        await message.answer("Введите хотя бы один навык:")
        return
    d = await message.state_peer.get_data() or {}
    d["skills"] = skills
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.PORTFOLIO)
    await message.answer(
        "Отправьте ссылку на портфолио (GitHub, Behance и т.д.)\n"
        "или нажмите «⏭️ Пропустить»:",
        keyboard=skip_kb(),
    )


@labeler.message(StateRule(StudentForm.PORTFOLIO))
async def student_portfolio(message: Message) -> None:
    d = await message.state_peer.get_data() or {}

    if message.text == "⏭️ Пропустить":
        d["portfolio"] = None
    elif validate_url(message.text.strip()):
        d["portfolio"] = message.text.strip()
    else:
        await message.answer(
            "Введите корректную ссылку (http://...) или нажмите «⏭️ Пропустить»:",
            keyboard=skip_kb(),
        )
        return

    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.DESCRIPTION)
    await message.answer("Напишите краткое описание — чем вы полезны:")


@labeler.message(StateRule(StudentForm.DESCRIPTION))
async def student_description(message: Message) -> None:
    if not validate_text_length(message.text, 10, 500):
        await message.answer("Описание от 10 до 500 символов:")
        return
    d = await message.state_peer.get_data() or {}
    d["description"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(StudentForm.GOAL)
    await message.answer("Выберите цель участия:", keyboard=student_goal_kb())


@labeler.message(StateRule(StudentForm.GOAL))
async def student_goal(message: Message) -> None:
    if message.text not in _GOAL_MAP:
        await message.answer("Выберите вариант из списка:", keyboard=student_goal_kb())
        return

    d = await message.state_peer.get_data() or {}
    d["goal"] = _GOAL_MAP[message.text]
    await message.state_peer.set_data(d)

    from bot.database.models import Student
    preview = Student(
        user_id=0, name=d["name"], surname=d["surname"], university=d["university"],
        year=d["year"], faculty=d["faculty"], directions=d.get("directions", []),
        tech_interests=d.get("tech_interests", []), skills=d.get("skills", []),
        portfolio=d.get("portfolio"), description=d["description"],
        goal=StudentGoal(d["goal"]),
    )
    await message.answer(
        f"Проверьте анкету:\n\n{fmt_student(preview)}\n\nВсё верно?",
        keyboard=confirm_kb(),
    )


@labeler.message(StateRule(StudentForm.GOAL), text="✅ Подтвердить")
async def student_save_confirm(message: Message) -> None:
    await _save_student(message)


# Перехватываем подтверждение из любого состояния через отдельный хэндлер
@labeler.message(text="✅ Подтвердить")
async def universal_confirm(message: Message) -> None:
    state = await message.state_peer.get()
    if state and "student" in str(state):
        await _save_student(message)
    elif state and "startup" in str(state):
        from bot.handlers.startup import save_startup
        await save_startup(message)
    elif state and "teacher" in str(state):
        from bot.handlers.teacher import save_teacher
        await save_teacher(message)
    elif state and "partner" in str(state):
        from bot.handlers.partner import save_partner
        await save_partner(message)
    else:
        await message.answer("Нечего подтверждать.", keyboard=back_kb())


async def _save_student(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    await message.state_peer.delete()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        existing = await get_student_by_user_id(session, user.id)
        if existing:
            await update_student(session, user.id, d)
        else:
            await create_student(session, user.id, d)

    await message.answer("✅ Анкета сохранена!", keyboard=main_menu_kb(UserRole.student))


@labeler.message(text="👤 Мой профиль")
async def show_student_profile(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user or user.role != UserRole.student:
            return
        profile = await get_student_by_user_id(session, user.id)
        if not profile:
            await message.answer("Анкета не найдена. Пройдите регистрацию.", keyboard=back_kb())
        else:
            await message.answer(fmt_student(profile), keyboard=main_menu_kb(UserRole.student))
