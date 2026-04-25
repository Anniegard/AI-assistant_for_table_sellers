from aiogram.fsm.state import State, StatesGroup


class RecommendationStates(StatesGroup):
    scenario = State()
    user_height = State()
    budget = State()
    monitors_count = State()
    pc_on_desk = State()
    desk_size = State()


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


class FAQStates(StatesGroup):
    waiting_question = State()
