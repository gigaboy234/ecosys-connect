from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

DIRECTIONS = ["IT", "Биохим", "Машиностроение", "Бизнес", "Дизайн", "Медицина", "Энергетика", "Другое"]
TECH_INTERESTS = ["AI/ML", "Web3", "Биотех", "Робототехника", "IoT", "AR/VR", "Кибербез", "Другое"]
STARTUP_NEEDS = ["Разработчик", "Дизайнер", "Маркетолог", "Аналитик", "Преподаватель-консультант", "Другое"]
HELP_TYPES = ["Научное руководство", "Консультации", "Рецензирование", "Менторство"]
TEACHER_FORMATS = ["Очно", "Онлайн", "Смешанно"]
STARTUP_STAGES = ["Идея", "MVP", "Прототип", "Масштабирование"]
STUDENT_GOALS = ["Ищу стартап", "Хочу создать стартап", "Хочу найти преподавателя"]


def _multi_select_kb(
    options: list[str],
    selected: list[str],
    prefix: str,
    done_data: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for opt in options:
        mark = "✅ " if opt in selected else ""
        builder.row(InlineKeyboardButton(
            text=f"{mark}{opt}",
            callback_data=f"{prefix}:{opt}",
        ))
    builder.row(InlineKeyboardButton(text="➡️ Готово", callback_data=done_data))
    return builder.as_markup()


def directions_kb(selected: list[str]) -> InlineKeyboardMarkup:
    return _multi_select_kb(DIRECTIONS, selected, "dir", "dir:done")


def tech_interests_kb(selected: list[str]) -> InlineKeyboardMarkup:
    return _multi_select_kb(TECH_INTERESTS, selected, "tech", "tech:done")


def startup_needs_kb(selected: list[str]) -> InlineKeyboardMarkup:
    return _multi_select_kb(STARTUP_NEEDS, selected, "need", "need:done")


def help_types_kb(selected: list[str]) -> InlineKeyboardMarkup:
    return _multi_select_kb(HELP_TYPES, selected, "help", "help:done")


def startup_stage_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for stage in STARTUP_STAGES:
        builder.row(InlineKeyboardButton(text=stage, callback_data=f"stage:{stage}"))
    return builder.as_markup()


def student_goal_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for goal in STUDENT_GOALS:
        builder.row(InlineKeyboardButton(text=goal, callback_data=f"goal:{goal}"))
    return builder.as_markup()


def teacher_format_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fmt in TEACHER_FORMATS:
        builder.row(InlineKeyboardButton(text=fmt, callback_data=f"fmt:{fmt}"))
    return builder.as_markup()


def skip_kb(skip_data: str = "skip") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=skip_data)]
    ])
