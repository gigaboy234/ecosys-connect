from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.students import create_student, get_student_by_user_id, update_student
from bot.database.crud.users import get_user_by_tg_id
from bot.keyboards.main_menu import back_to_menu_kb, confirm_kb
from bot.keyboards.registration import (
    directions_kb,
    skip_kb,
    student_goal_kb,
    tech_interests_kb,
)
from bot.states.student_states import StudentForm
from bot.utils.formatters import fmt_student
from bot.utils.validators import parse_comma_list, validate_text_length, validate_url, validate_year

router = Router()

_GOAL_MAP = {
    "Ищу стартап": "find_startup",
    "Хочу создать стартап": "create_startup",
    "Хочу найти преподавателя": "find_teacher",
}


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(StudentForm.name)
    await state.update_data(directions=[], tech_interests=[])
    await message.answer("📝 <b>Регистрация студента</b>\n\nВведите ваше <b>имя</b>:", parse_mode="HTML")


@router.message(StudentForm.name)
async def student_name(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 50):
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуйте ещё раз:")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(StudentForm.surname)
    await message.answer("Введите вашу <b>фамилию</b>:", parse_mode="HTML")


@router.message(StudentForm.surname)
async def student_surname(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 50):
        await message.answer("Фамилия должна быть от 2 до 50 символов. Попробуйте ещё раз:")
        return
    await state.update_data(surname=message.text.strip())
    await state.set_state(StudentForm.university)
    await message.answer("Введите название вашего <b>учебного заведения</b>:", parse_mode="HTML")


@router.message(StudentForm.university)
async def student_university(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 3, 128):
        await message.answer("Введите корректное название учебного заведения:")
        return
    await state.update_data(university=message.text.strip())
    await state.set_state(StudentForm.year)
    await message.answer("Введите ваш <b>курс</b> (1–6):", parse_mode="HTML")


@router.message(StudentForm.year)
async def student_year(message: Message, state: FSMContext) -> None:
    year = validate_year(message.text)
    if year is None:
        await message.answer("Курс должен быть числом от 1 до 6. Попробуйте ещё раз:")
        return
    await state.update_data(year=year)
    await state.set_state(StudentForm.faculty)
    await message.answer("Введите ваш <b>факультет/кафедру</b>:", parse_mode="HTML")


@router.message(StudentForm.faculty)
async def student_faculty(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректное название факультета:")
        return
    await state.update_data(faculty=message.text.strip())
    await state.set_state(StudentForm.directions)
    data = await state.get_data()
    await message.answer(
        "Выберите ваши <b>направления</b> (можно несколько):",
        reply_markup=directions_kb(data.get("directions", [])),
        parse_mode="HTML",
    )


@router.callback_query(StudentForm.directions, F.data.startswith("dir:"))
async def student_directions_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    if value == "done":
        data = await state.get_data()
        if not data.get("directions"):
            await callback.answer("Выберите хотя бы одно направление!", show_alert=True)
            return
        await state.set_state(StudentForm.tech_interests)
        await callback.message.edit_text(
            "Выберите ваши <b>технологические интересы</b> (можно несколько):",
            reply_markup=tech_interests_kb([]),
            parse_mode="HTML",
        )
    else:
        data = await state.get_data()
        dirs = data.get("directions", [])
        if value in dirs:
            dirs.remove(value)
        else:
            dirs.append(value)
        await state.update_data(directions=dirs)
        await callback.message.edit_reply_markup(reply_markup=directions_kb(dirs))
    await callback.answer()


@router.callback_query(StudentForm.tech_interests, F.data.startswith("tech:"))
async def student_tech_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    if value == "done":
        await state.set_state(StudentForm.skills)
        await callback.message.edit_text(
            "Введите ваши <b>навыки</b> через запятую:\n"
            "<i>Пример: Python, SQL, Figma</i>",
            parse_mode="HTML",
        )
    else:
        data = await state.get_data()
        tech = data.get("tech_interests", [])
        if value in tech:
            tech.remove(value)
        else:
            tech.append(value)
        await state.update_data(tech_interests=tech)
        await callback.message.edit_reply_markup(reply_markup=tech_interests_kb(tech))
    await callback.answer()


@router.message(StudentForm.skills)
async def student_skills(message: Message, state: FSMContext) -> None:
    skills = parse_comma_list(message.text)
    if not skills:
        await message.answer("Введите хотя бы один навык:")
        return
    await state.update_data(skills=skills)
    await state.set_state(StudentForm.portfolio)
    await message.answer(
        "Отправьте ссылку на ваше <b>портфолио</b> (GitHub, Behance и т.д.)\n"
        "или нажмите «Пропустить»:",
        reply_markup=skip_kb("skip_portfolio"),
        parse_mode="HTML",
    )


@router.callback_query(StudentForm.portfolio, F.data == "skip_portfolio")
async def student_portfolio_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(portfolio=None)
    await state.set_state(StudentForm.description)
    await callback.message.edit_text(
        "Напишите краткое <b>описание</b> — чем вы можете быть полезны:", parse_mode="HTML"
    )
    await callback.answer()


@router.message(StudentForm.portfolio)
async def student_portfolio(message: Message, state: FSMContext) -> None:
    if not validate_url(message.text.strip()):
        await message.answer(
            "Введите корректную ссылку (начинается с http:// или https://) "
            "или нажмите «Пропустить»:",
            reply_markup=skip_kb("skip_portfolio"),
        )
        return
    await state.update_data(portfolio=message.text.strip())
    await state.set_state(StudentForm.description)
    await message.answer(
        "Напишите краткое <b>описание</b> — чем вы можете быть полезны:", parse_mode="HTML"
    )


@router.message(StudentForm.description)
async def student_description(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 10, 500):
        await message.answer("Описание должно быть от 10 до 500 символов:")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(StudentForm.goal)
    await message.answer(
        "Выберите вашу <b>цель участия</b>:",
        reply_markup=student_goal_kb(),
        parse_mode="HTML",
    )


@router.callback_query(StudentForm.goal, F.data.startswith("goal:"))
async def student_goal(callback: CallbackQuery, state: FSMContext) -> None:
    goal_label = callback.data.split(":", 1)[1]
    goal_value = _GOAL_MAP.get(goal_label, "find_startup")
    await state.update_data(goal=goal_value)
    await state.set_state(StudentForm.confirm)

    data = await state.get_data()
    from bot.database.models import Student, StudentGoal

    preview = Student(
        user_id=0,
        name=data["name"],
        surname=data["surname"],
        university=data["university"],
        year=data["year"],
        faculty=data["faculty"],
        directions=data.get("directions", []),
        tech_interests=data.get("tech_interests", []),
        skills=data.get("skills", []),
        portfolio=data.get("portfolio"),
        description=data["description"],
        goal=StudentGoal(data["goal"]),
    )

    await callback.message.edit_text(
        f"<b>Проверьте вашу анкету:</b>\n\n{fmt_student(preview)}\n\n"
        f"Всё верно?",
        reply_markup=confirm_kb("student:save", "menu:main"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "student:save")
async def student_save(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    user = await get_user_by_tg_id(session, callback.from_user.id)
    existing = await get_student_by_user_id(session, user.id)

    if existing:
        await update_student(session, user.id, data)
    else:
        await create_student(session, user.id, data)

    from bot.keyboards.main_menu import main_menu_kb
    from bot.database.models import UserRole

    await callback.message.edit_text(
        "✅ <b>Анкета сохранена!</b>\n\nТеперь вы можете искать стартапы и преподавателей.",
        reply_markup=main_menu_kb(UserRole.student),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def show_profile(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)
    if user.role.value == "student":
        profile = await get_student_by_user_id(session, user.id)
        if not profile:
            await callback.message.edit_text(
                "Анкета не найдена. Пройдите регистрацию.",
                reply_markup=back_to_menu_kb(),
            )
        else:
            await callback.message.edit_text(
                fmt_student(profile),
                reply_markup=back_to_menu_kb(),
                parse_mode="HTML",
            )
    await callback.answer()
