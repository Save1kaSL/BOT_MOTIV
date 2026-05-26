from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    waiting_ip = State()


class ApplicationForm(StatesGroup):
    waiting_form = State()
    waiting_inn = State()
    waiting_full_name = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_city = State()


class StepProgress(StatesGroup):
    waiting_step_screenshot = State()
    waiting_final_screenshots = State()


class AdminContact(StatesGroup):
    waiting_message_to_user = State()


class PayoutDetails(StatesGroup):
    waiting_requisites = State()


class AdminSearch(StatesGroup):
    waiting_query = State()


class AdminFinance(StatesGroup):
    waiting_hold_user_id = State()
    waiting_hold_value = State()


class UserContact(StatesGroup):
    waiting_username = State()
    waiting_username_for_cd = State()


class UserSupport(StatesGroup):
    waiting_message = State()
