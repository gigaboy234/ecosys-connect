from aiogram.fsm.state import State, StatesGroup


class PartnerForm(StatesGroup):
    company_name = State()
    sphere = State()
    needs = State()
    resources = State()
    contact_person = State()
    confirm = State()


class PartnerEdit(StatesGroup):
    choose_field = State()
    edit_value = State()
