from aiogram.fsm.state import State, StatesGroup


class LeadCollectionStates(StatesGroup):
    budget = State()
    user_height = State()
    monitors_count = State()
    use_case = State()
    contact = State()
