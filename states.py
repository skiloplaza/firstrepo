from aiogram.fsm.state import State, StatesGroup


class Checkout(StatesGroup):
    phone   = State()
    address = State()
    note    = State()
    confirm = State()


class Search(StatesGroup):
    query = State()


class Calculator(StatesGroup):
    price    = State()
    quantity = State()


class AdminProduct(StatesGroup):
    category    = State()
    name        = State()
    description = State()
    price       = State()
    old_price   = State()
    stock       = State()
    confirm     = State()
    edit_field  = State()
    edit_value  = State()


class AdminBroadcast(StatesGroup):
    content = State()
    confirm = State()


class AdminUserMsg(StatesGroup):
    message = State()


class AdminChannel(StatesGroup):
    username = State()
    title    = State()
    url      = State()
