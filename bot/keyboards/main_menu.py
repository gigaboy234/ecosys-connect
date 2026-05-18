import json

from vkbottle import Keyboard, KeyboardButtonColor, Text

from bot.database.models import UserRole


def role_selection_kb() -> str:
    kb = Keyboard(one_time=True)
    kb.add(Text("🎓 Студент"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("🚀 Стартап"), color=KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("👨‍🏫 Преподаватель"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("🏭 Партнёр"), color=KeyboardButtonColor.PRIMARY)
    return kb.get_json()


def main_menu_kb(role: UserRole) -> str:
    kb = Keyboard(one_time=False)

    if role == UserRole.student:
        kb.add(Text("👤 Мой профиль"), color=KeyboardButtonColor.SECONDARY)
        kb.add(Text("🚀 Найти стартап"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        kb.add(Text("👨‍🏫 Найти преподавателя"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("➕ Создать стартап"), color=KeyboardButtonColor.POSITIVE)
        kb.row()
        kb.add(Text("📬 Входящие заявки"), color=KeyboardButtonColor.SECONDARY)
        kb.add(Text("🔄 Сменить роль"), color=KeyboardButtonColor.NEGATIVE)

    elif role == UserRole.startup:
        kb.add(Text("🚀 Мой стартап"), color=KeyboardButtonColor.SECONDARY)
        kb.add(Text("👥 Команда"), color=KeyboardButtonColor.SECONDARY)
        kb.row()
        kb.add(Text("👨‍🏫 Найти наставника"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("🏭 Найти партнёра"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        kb.add(Text("📬 Входящие заявки"), color=KeyboardButtonColor.SECONDARY)
        kb.add(Text("🔄 Сменить роль"), color=KeyboardButtonColor.NEGATIVE)

    elif role == UserRole.teacher:
        kb.add(Text("👤 Мой профиль"), color=KeyboardButtonColor.SECONDARY)
        kb.add(Text("🚀 Найти стартап"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        kb.add(Text("🎓 Найти студента"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("📬 Входящие заявки"), color=KeyboardButtonColor.SECONDARY)
        kb.row()
        kb.add(Text("🔄 Сменить роль"), color=KeyboardButtonColor.NEGATIVE)

    elif role == UserRole.partner:
        kb.add(Text("🏭 Мой профиль"), color=KeyboardButtonColor.SECONDARY)
        kb.add(Text("🚀 Найти стартап"), color=KeyboardButtonColor.PRIMARY)
        kb.row()
        kb.add(Text("🎓 Найти студента"), color=KeyboardButtonColor.PRIMARY)
        kb.add(Text("📬 Входящие заявки"), color=KeyboardButtonColor.SECONDARY)
        kb.row()
        kb.add(Text("🔄 Сменить роль"), color=KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


def back_kb() -> str:
    kb = Keyboard(one_time=False)
    kb.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def confirm_kb() -> str:
    kb = Keyboard(one_time=True)
    kb.add(Text("✅ Подтвердить"), color=KeyboardButtonColor.POSITIVE)
    kb.add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()


def yes_no_kb() -> str:
    kb = Keyboard(one_time=True)
    kb.add(Text("✅ Да"), color=KeyboardButtonColor.POSITIVE)
    kb.add(Text("❌ Нет"), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()


def empty_kb() -> str:
    return Keyboard(one_time=True).get_json()
