from aiogram.fsm.state import State, StatesGroup

class Application(StatesGroup):
    """
    FSM States for the Application flow.
    """
    name = State()              # User's name
    business_type = State()     # Type of business
    task_description = State()  # What to automate
    contact_info = State()      # Contact details
    submitted = State()         # Application submitted, waiting in menu
