from vkbottle import Keyboard, KeyboardButtonColor, Text

DIRECTIONS = ["IT", "Биохим", "Машиностроение", "Бизнес", "Дизайн", "Медицина", "Другое"]
TECH_INTERESTS = ["AI/ML", "Web3", "Биотех", "Робототехника", "IoT", "AR/VR", "Другое"]
STARTUP_NEEDS = ["Разработчик", "Дизайнер", "Маркетолог", "Аналитик", "Консультант", "Другое"]
HELP_TYPES = ["Научное руководство", "Консультации", "Рецензирование", "Менторство"]
TEACHER_FORMATS = ["Очно", "Онлайн", "Смешанно"]
STARTUP_STAGES = ["Идея", "MVP", "Прототип", "Масштабирование"]
STUDENT_GOALS = ["Ищу стартап", "Хочу создать стартап", "Хочу найти преподавателя"]


def _multi_select_kb(options: list[str], selected: list[str]) -> str:
    kb = Keyboard(one_time=False)
    for i, opt in enumerate(options):
        mark = "✅ " if opt in selected else ""
        kb.add(Text(f"{mark}{opt}"), color=KeyboardButtonColor.PRIMARY if opt in selected else KeyboardButtonColor.SECONDARY)
        if (i + 1) % 2 == 0:
            kb.row()
    kb.row()
    kb.add(Text("➡️ Готово"), color=KeyboardButtonColor.POSITIVE)
    return kb.get_json()


def directions_kb(selected: list[str]) -> str:
    return _multi_select_kb(DIRECTIONS, selected)


def tech_interests_kb(selected: list[str]) -> str:
    return _multi_select_kb(TECH_INTERESTS, selected)


def startup_needs_kb(selected: list[str]) -> str:
    return _multi_select_kb(STARTUP_NEEDS, selected)


def help_types_kb(selected: list[str]) -> str:
    return _multi_select_kb(HELP_TYPES, selected)


def options_kb(options: list[str]) -> str:
    kb = Keyboard(one_time=True)
    for i, opt in enumerate(options):
        kb.add(Text(opt), color=KeyboardButtonColor.PRIMARY)
        if (i + 1) % 2 == 0 and i < len(options) - 1:
            kb.row()
    return kb.get_json()


def startup_stage_kb() -> str:
    return options_kb(STARTUP_STAGES)


def student_goal_kb() -> str:
    return options_kb(STUDENT_GOALS)


def teacher_format_kb() -> str:
    return options_kb(TEACHER_FORMATS)


def skip_kb() -> str:
    kb = Keyboard(one_time=True)
    kb.add(Text("⏭️ Пропустить"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()
