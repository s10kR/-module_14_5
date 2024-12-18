from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import crud_functions
from crud_functions import *

crud_functions.initiate_db()
for i in range(1, 5):
    cursor.execute("INSERT INTO Products (title, description, price) VALUES (?, ?, ?)",
                   (f'Продукт {i}', f'Описание {i}', i * 100))

api = "7505996508:AAFo79GlOzYuWxZQ2mC34mhL6o1M3Na7x6E"
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

kb = ReplyKeyboardMarkup(resize_keyboard=True)
button_1 = KeyboardButton(text='Рассчитать')
button_2 = KeyboardButton(text='Информация')
button_3 = KeyboardButton(text='Купить')
button_4 = KeyboardButton(text='Регистрация')
kb.add(button_1)
kb.add(button_2)
kb.add(button_3)
kb.add(button_4)

ikb = InlineKeyboardMarkup()
i_button_1 = InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories')
i_button_2 = InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas')
ikb.add(i_button_1)
ikb.add(i_button_2)

products_ikb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Product1', callback_data="product_buying")],
        [InlineKeyboardButton(text='Product2', callback_data="product_buying")],
        [InlineKeyboardButton(text='Product3', callback_data="product_buying")],
        [InlineKeyboardButton(text='Product4', callback_data="product_buying")]
    ]
)


@dp.message_handler(text="Купить")
async def get_buying_list(message):
    for product in get_all_products():
        await message.answer(f"Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}")
        with open(f'{product[0]}.png', 'rb') as img:
            await message.answer_photo(img)
    await message.answer('Выберите продукт для покупки:', reply_markup=products_ikb)


@dp.callback_query_handler(text="product_buying")
async def send_confirm_message(call):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()


class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()


class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = 1000


@dp.message_handler(text='Рассчитать')
async def main_menu(message):
    await message.answer('Выберите опцию:', reply_markup=ikb)


@dp.callback_query_handler(text='formulas')
async def get_formulas(call):
    await call.message.answer('для мужчин: 10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5;'
                              'для женщин: 10 x вес (кг) + 6,25 x рост (см) – 5 x возраст (г) – 161.')
    await call.answer()


@dp.message_handler(commands=['start'])
async def start(message):
    await message.answer('Привет! Я бот помогающий твоему здоровью.', reply_markup=kb)


@dp.callback_query_handler(text='calories')
async def set_age(call):
    await call.message.answer('Введите свой возраст:')
    await UserState.age.set()
    await call.answer()


@dp.message_handler(state=UserState.age)
async def set_growth(message, state):
    await state.update_data(age=message.text)
    await message.answer('Введите свой рост:')
    await UserState.growth.set()


@dp.message_handler(state=UserState.growth)
async def set_weight(message, state):
    await state.update_data(growth=message.text)
    await message.answer('Введите свой вес:')
    await UserState.weight.set()


@dp.message_handler(state=UserState.weight)
async def set_weight(message, state):
    await state.update_data(weight=message.text)
    data = await state.get_data()
    result_men = 10 * int(data['weight']) + 6.25 * int(data['growth']) - 5 * int(data['age']) + 5
    result_women = 10 * int(data['weight']) + 6.25 * int(data['growth']) - 5 * int(data['age']) - 161
    await message.answer(f'Ваша норма калорий если вы мужчина {result_men}, если женщина - {result_women}')
    await state.finish()


@dp.message_handler(text="Регистрация")
async def sign_up(message):
    await  message.answer('Введите имя пользователя (только латинский алфавит):', reply_markup=kb)
    await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.username)
async def set_username(message, state):
    if not is_included(message.text):
        await state.update_data(username=message.text)
        await message.answer('Введите свой email:')
        await RegistrationState.email.set()
    else:
        await message.answer('Пользователь существует, введите другое имя')
        await RegistrationState.username.set()


@dp.message_handler(state=RegistrationState.email)
async def set_email(message, state):
    await state.update_data(email=message.text)
    await message.answer('Введите свой возраст:')
    await RegistrationState.age.set()


@dp.message_handler(state=RegistrationState.age)
async def set_age(message, state):
    await state.update_data(age=message.text)
    data = await state.get_data()
    add_user(data['username'], data['email'], data['age'])
    await message.answer('Регистрация прошла успешно')
    await state.finish()


@dp.message_handler()
async def all_messages(message):
    await message.answer('Введите команду /start, чтобы начать общение.')


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    connection.commit()
    connection.close()