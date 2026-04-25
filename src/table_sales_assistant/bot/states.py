from aiogram.fsm.state import State, StatesGroup


class RecommendationStates(StatesGroup):
    budget = State()
    user_height = State()
    monitors_count = State()


class FAQStates(StatesGroup):
    waiting_question = State()


class LeadCollectionStates(StatesGroup):
    name = State()
    phone = State()
    city = State()
    height_cm = State()
    budget = State()
    use_case = State()
    monitors_count = State()
    has_pc_case = State()
    preferred_size = State()
    needs_delivery = State()
    needs_assembly = State()
    comment = State()
