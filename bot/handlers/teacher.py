from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.teachers import create_teacher, get_teacher_by_user_id, update_teacher
from bot.database.crud.users import get_user_by_tg_id
from bot.keyboards.main_menu import back_to_menu_kb, confirm_kb
from bot.keyboards.registration import help_types_kb, teacher_format_kb
from bot.states.teacher_states import TeacherForm
from bot.utils.formatters import fmt_teacher
from bot.utils.validators import parse_comma_list, validate_availability, validate_text_length

router = Router()

_FORMAT_MAP = {"Очно": "offline", "Онлайн": "online", "Смешанно": "mixed"}


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(TeacherForm.full_name)
    await state.update_data(research_directions=[], competencies=[], help_types=[])
    await message.answer(
        "📝 <b>Регистрация преподавателя</b>\n\nВведите ваше <b>ФИО</b>:",
        parse_mode="HTML",
    )


@router.message(TeacherForm.full_name)
async def teacher_fullname(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 5, 128):
        await message.answer("Введите полное ФИО (от 5 до 128 символов):")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(TeacherForm.degree)
    await message.answer("Введите вашу <b>учёную степень / должность</b>:", parse_mode="HTML")


@router.message(TeacherForm.degree)
async def teacher_degree(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректную степень/должность:")
        return
    await state.update_data(degree=message.text.strip())
    await state.set_state(TeacherForm.department)
    await message.answer("Введите <b>кафедру / направление исследований</b>:", parse_mode="HTML")


@router.message(TeacherForm.department)
async def teacher_department(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректное название кафедры:")
        return
    await state.update_data(department=message.text.strip())
    await state.set_state(TeacherForm.research_directions)
    await message.answer(
        "Введите ваши <b>научные направления</b> через запятую:\n"
        "<i>Пример: AI, Биотехнологии, Робототехника</i>",
        parse_mode="HTML",
    )


@router.message(TeacherForm.research_directions)
async def teacher_directions(message: Message, state: FSMContext) -> None:
    dirs = parse_comma_list(message.text)
    if not dirs:
        await message.answer("Введите хотя бы одно направление:")
        return
    await state.update_data(research_directions=dirs)
    await state.set_state(TeacherForm.competencies)
    await message.answer(
        "Введите ваши <b>технологические компетенции</b> через запятую:\n"
        "<i>Пример: Python, TensorFlow, MATLAB</i>",
        parse_mode="HTML",
    )


@router.message(TeacherForm.competencies)
async def teacher_competencies(message: Message, state: FSMContext) -> None:
    comp = parse_comma_list(message.text)
    if not comp:
        await message.answer("Введите хотя бы одну компетенцию:")
        return
    await state.update_data(competencies=comp)
    await state.set_state(TeacherForm.help_types)
    await message.answer(
        "Выберите, <b>чем вы можете помочь</b> (можно несколько):",
        reply_markup=help_types_kb([]),
        parse_mode="HTML",
    )


@router.callback_query(TeacherForm.help_types, F.data.startswith("help:"))
async def teacher_help_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    if value == "done":
        data = await state.get_data()
        if not data.get("help_types"):
            await callback.answer("Выберите хотя бы один тип помощи!", show_alert=True)
            return
        await state.set_state(TeacherForm.availability)
        await callback.message.edit_text(
            "Введите вашу <b>доступность</b> (часов в неделю, число от 1 до 40):",
            parse_mode="HTML",
        )
    else:
        data = await state.get_data()
        help_t = data.get("help_types", [])
        if value in help_t:
            help_t.remove(value)
        else:
            help_t.append(value)
        await state.update_data(help_types=help_t)
        await callback.message.edit_reply_markup(reply_markup=help_types_kb(help_t))
    await callback.answer()


@router.message(TeacherForm.availability)
async def teacher_availability(message: Message, state: FSMContext) -> None:
    hours = validate_availability(message.text)
    if hours is None:
        await message.answer("Введите число часов от 1 до 168:")
        return
    await state.update_data(availability=hours)
    await state.set_state(TeacherForm.format)
    await message.answer(
        "Выберите <b>формат участия</b>:",
        reply_markup=teacher_format_kb(),
        parse_mode="HTML",
    )


@router.callback_query(TeacherForm.format, F.data.startswith("fmt:"))
async def teacher_format(callback: CallbackQuery, state: FSMContext) -> None:
    fmt_label = callback.data.split(":", 1)[1]
    fmt_value = _FORMAT_MAP.get(fmt_label, "online")
    await state.update_data(format=fmt_value)
    await state.set_state(TeacherForm.confirm)

    data = await state.get_data()
    from bot.database.models import Teacher, TeacherFormat

    preview = Teacher(
        user_id=0,
        full_name=data["full_name"],
        degree=data["degree"],
        department=data["department"],
        research_directions=data.get("research_directions", []),
        competencies=data.get("competencies", []),
        help_types=data.get("help_types", []),
        availability=data["availability"],
        format=TeacherFormat(data["format"]),
    )

    await callback.message.edit_text(
        f"<b>Проверьте вашу анкету:</b>\n\n{fmt_teacher(preview)}\n\nВсё верно?",
        reply_markup=confirm_kb("teacher:save", "menu:main"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "teacher:save")
async def teacher_save(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    user = await get_user_by_tg_id(session, callback.from_user.id)
    existing = await get_teacher_by_user_id(session, user.id)

    if existing:
        await update_teacher(session, user.id, data)
    else:
        await create_teacher(session, user.id, data)

    from bot.keyboards.main_menu import main_menu_kb
    from bot.database.models import UserRole

    await callback.message.edit_text(
        "✅ <b>Анкета преподавателя сохранена!</b>",
        reply_markup=main_menu_kb(UserRole.teacher),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def show_teacher_profile(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)
    from bot.database.models import UserRole
    if user.role != UserRole.teacher:
        return
    profile = await get_teacher_by_user_id(session, user.id)
    if not profile:
        await callback.message.edit_text(
            "Анкета не найдена.", reply_markup=back_to_menu_kb()
        )
    else:
        await callback.message.edit_text(
            fmt_teacher(profile), reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
    await callback.answer()
