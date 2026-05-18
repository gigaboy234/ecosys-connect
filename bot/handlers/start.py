from vkbottle.bot import BotLabeler, Message

from bot.database.crud.users import get_or_create_user, set_user_role
from bot.database.db import AsyncSessionLocal
from bot.database.models import UserRole
from bot.keyboards.main_menu import (
    back_kb,
    main_menu_kb,
    role_selection_kb,
    yes_no_kb,
)

labeler = BotLabeler()

_ROLE_MAP = {
    "🎓 Студент": UserRole.student,
    "🚀 Стартап": UserRole.startup,
    "👨‍🏫 Преподаватель": UserRole.teacher,
    "🏭 Партнёр": UserRole.partner,
}

_ROLE_LABELS = {
    UserRole.student: "🎓 Студент",
    UserRole.startup: "🚀 Стартап",
    UserRole.teacher: "👨‍🏫 Преподаватель",
    UserRole.partner: "🏭 Индустриальный партнёр",
}


@labeler.message(text=["начать", "start", "/start", "привет", "🏠 Главное меню"])
async def cmd_start(message: Message) -> None:
    await message.state_peer.delete()
    async with AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(session, message.from_id, None)

        if user.is_banned:
            await message.answer("🚫 Ваш аккаунт заблокирован.")
            return

        if user.role:
            await message.answer(
                f"👋 С возвращением!\n\nВыберите действие:",
                keyboard=main_menu_kb(user.role),
            )
        else:
            await message.answer(
                "👋 Добро пожаловать в EcoSys Connect!\n\n"
                "Это платформа для знакомства студентов, стартапов, "
                "преподавателей и индустриальных партнёров.\n\n"
                "Выберите вашу роль:",
                keyboard=role_selection_kb(),
            )


@labeler.message(text=list(_ROLE_MAP.keys()))
async def choose_role(message: Message) -> None:
    role = _ROLE_MAP[message.text]

    async with AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(session, message.from_id, None)

        if user.role and user.role != role:
            await message.state_peer.set_data({"pending_role": role.value})
            await message.answer(
                f"⚠️ У вас уже есть профиль ({_ROLE_LABELS[user.role]}).\n"
                "Смена роли сбросит текущую анкету. Продолжить?",
                keyboard=yes_no_kb(),
            )
            return

        await _apply_role(message, session, role)


@labeler.message(text="✅ Да")
async def confirm_yes(message: Message) -> None:
    state_data = await message.state_peer.get_data()
    pending_role = state_data.get("pending_role") if state_data else None

    if not pending_role:
        await message.answer("Нечего подтверждать.", keyboard=back_kb())
        return

    async with AsyncSessionLocal() as session:
        role = UserRole(pending_role)
        await _apply_role(message, session, role)


@labeler.message(text="❌ Нет")
async def confirm_no(message: Message) -> None:
    await message.state_peer.delete()
    async with AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(session, message.from_id, None)
        if user.role:
            await message.answer("Отмена.", keyboard=main_menu_kb(user.role))
        else:
            await message.answer("Отмена.", keyboard=role_selection_kb())


@labeler.message(text="🔄 Сменить роль")
async def change_role(message: Message) -> None:
    await message.state_peer.delete()
    await message.answer(
        "Выберите новую роль (текущая анкета будет сброшена):",
        keyboard=role_selection_kb(),
    )


async def _apply_role(message: Message, session, role: UserRole) -> None:
    await set_user_role(session, message.from_id, role)
    await message.answer(
        f"Отлично! Роль: {_ROLE_LABELS[role]}\n\nТеперь заполним анкету.",
    )

    from bot.handlers import student, startup, teacher, partner

    starters = {
        UserRole.student: student.start_registration,
        UserRole.startup: startup.start_registration,
        UserRole.teacher: teacher.start_registration,
        UserRole.partner: partner.start_registration,
    }
    await starters[role](message)
