from aiogram.fsm.state import State, StatesGroup


class TeacherForm(StatesGroup):
    full_name = State()
    degree = State()
    department = State()
    research_directions = State()
    competencies = State()
    help_types = State()
    availability = State()
    format = State()
    confirm = State()


class TeacherEdit(StatesGroup):
    choose_field = State()
    edit_value = State()
