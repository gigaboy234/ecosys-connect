from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.users import get_or_create_user, set_user_role
from bot.database.models import UserRole
from bot.keyboards.main_menu import main_menu_kb, role_selection_kb, yes_no_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user, created = await get_or_create_user(
        session, message.from_user.id, message.from_user.username
    )

    if user.is_banned:
        await message.answer("🚫 Ваш аккаунт заблокирован.")
        return

    if user.role:
        await message.answer(
            f"👋 С возвращением!\n\nВыберите действие:",
            reply_markup=main_menu_kb(user.role),
        )
    else:
        await message.answer(
            "👋 Добро пожаловать в <b>EcoSys Connect</b>!\n\n"
            "Это платформа для знакомства студентов, стартапов, "
            "преподавателей и индустриальных партнёров.\n\n"
            "Выберите свою роль:",
            reply_markup=role_selection_kb(),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("role:"))
async def choose_role(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    role_str = callback.data.split(":")[1]
    role = UserRole(role_str)

    user, _ = await get_or_create_user(
        session, callback.from_user.id, callback.from_user.username
    )

    if user.role and user.role != role:
        await callback.message.edit_text(
            "⚠️ У вас уже есть профиль. Смена роли удалит текущую анкету. Продолжить?",
            reply_markup=yes_no_kb(f"confirm_role:{role_str}", "menu:main"),
        )
        return

    await _apply_role(callback, session, state, role)


@router.callback_query(F.data.startswith("confirm_role:"))
async def confirm_role_change(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    role_str = callback.data.split(":")[1]
    role = UserRole(role_str)
    await _apply_role(callback, session, state, role)


async def _apply_role(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    role: UserRole,
) -> None:
    await set_user_role(session, callback.from_user.id, role)

    role_labels = {
        UserRole.student: "🎓 Студент",
        UserRole.startup: "🚀 Стартап",
        UserRole.teacher: "👨‍🏫 Преподаватель",
        UserRole.partner: "🏭 Индустриальный партнёр",
    }

    await callback.message.edit_text(
        f"Отлично! Вы выбрали роль: <b>{role_labels[role]}</b>\n\n"
        "Теперь заполните анкету, чтобы другие участники могли вас найти.",
        parse_mode="HTML",
    )

    # Перенаправляем на регистрацию нужной роли
    from bot.handlers import student, startup, teacher, partner

    starters = {
        UserRole.student: student.start_registration,
        UserRole.startup: startup.start_registration,
        UserRole.teacher: teacher.start_registration,
        UserRole.partner: partner.start_registration,
    }
    await starters[role](callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user, _ = await get_or_create_user(
        session, callback.from_user.id, callback.from_user.username
    )
    if not user.role:
        await callback.message.edit_text(
            "Выберите роль:", reply_markup=role_selection_kb()
        )
    else:
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>",
            reply_markup=main_menu_kb(user.role),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "menu:change_role")
async def change_role_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Выберите новую роль (текущая анкета будет сброшена):",
        reply_markup=role_selection_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
