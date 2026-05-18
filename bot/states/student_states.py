from aiogram.fsm.state import State, StatesGroup


class StudentForm(StatesGroup):
    name = State()
    surname = State()
    university = State()
    year = State()
    faculty = State()
    directions = State()
    tech_interests = State()
    skills = State()
    portfolio = State()
    description = State()
    goal = State()
    confirm = State()


class StudentEdit(StatesGroup):
    choose_field = State()
    edit_value = State()
