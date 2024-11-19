import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from source import keyboards as kb
import yaml
from dotenv import load_dotenv
from aiogram import F
import os
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from source import functions as funcs

load_dotenv()
global YUAN_RATE
YUAN_RATE = float(os.getenv('YUAN_RATE'))
TOKEN_API = os.getenv('TOKEN_API')
tariffs = funcs.load_tariffs()

bot = Bot(TOKEN_API)
dp = Dispatcher()
with open("source/texts.yaml", "r", encoding="utf-8") as file:
    text = yaml.safe_load(file)


@dp.message(Command("start"))
async def beginning(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id, text=text['menu']['message'],
                           reply_markup=kb.main_keyboard(chat_id=chat_id),
                           parse_mode='Markdown')


# format_data = {
#                 "fio": user_data[1],
#                 "gender": json_data["sex"],
#                 "phone": json_data["phone"],
#                 "status": json_data["status"],
#                 "adult": 'Да' if json_data["is_adult"] else 'Нет',
#                 "cstati": 'Да' if json_data["is_cstati"] else 'Нет',
#             }
#             await bot_sender.send_message(message.chat.id, messages["commands"]["mydata"].format(**format_data))
#
#
#

class Calculator(StatesGroup):
    price_yuan = State()
    category = State()
    del_way = State()


@dp.callback_query(F.data.startswith('calculate'))
async def begin_calculation(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(text=text["calculator"]["enter_price"],
                           chat_id=callback.from_user.id,
                           parse_mode='Markdown')
    await state.set_state(Calculator.price_yuan)

@dp.message(Calculator.price_yuan)
async def set_price(message: types.Message, state: FSMContext):
    try:
        price_yuan = float(message.text)
        await state.update_data(price_yuan=price_yuan)
        await state.set_state(Calculator.category)
        await bot.send_message(chat_id=message.chat.id,
                               text=text["calculator"]["choose_category"],
                               reply_markup=kb.categories_keyboard(tariffs['tariffs']),
                               parse_mode='Markdown'
                               )
    except:
        await bot.send_message(chat_id=message.chat.id,
                               text=text["calculator"]["enter_price_error"],
                               parse_mode='Markdown'
                               )
        await state.clear()

@dp.callback_query(Calculator.category)
async def set_delivery(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data)
    cat_id = callback.data
    data = await state.get_data()
    category_info = tariffs['tariffs'][cat_id]
    product_info = {
        "price_yuan": data['price_yuan'],
        "price_rub": data['price_yuan'] * YUAN_RATE,
        "del_avia_price": category_info['avia'],
        "del_avia_duration": '-'.join(tariffs['delivery_time']['avia']),
        "del_auto_price": category_info['auto'],
        "del_auto_duration": '-'.join(tariffs['delivery_time']['auto'])
    }
    await bot.send_message(chat_id=callback.from_user.id,
                           text=text["calculator"]["choose_delivery"].format(**product_info),
                           reply_markup=kb.del_type_keyboard(tariffs['tariffs'], cat_id),
                           parse_mode='Markdown'
                           )
    await state.set_state(Calculator.del_way)

@dp.callback_query(Calculator.del_way)
async def set_delivery(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(del_way=callback.data)
    data = await state.get_data()
    category_info = tariffs['tariffs'][data['category']]
    order_info = {
        "category": category_info['category'],
        "price_yuan": data['price_yuan'],
        "price_rub": data['price_yuan'] * YUAN_RATE,
        "del_way": data['del_way'],
        "final_price": data['price_yuan'] * YUAN_RATE * (1 if data['price_yuan'] < 1500 else 1.03) * 1.08 + category_info[data['del_way']],
    }

    await bot.send_message(chat_id=callback.from_user.id,text=text["calculator"]["final_price"].format(**order_info),
                           reply_markup=kb.calculator_last_keyboard(),
                           parse_mode='Markdown')


class RateState(StatesGroup):
    rate = State()


@dp.callback_query(F.data.startswith('set_rate'))
async def set_rate(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(text=f'Текущий курс юаня — *{YUAN_RATE}*\n\n Введите новый курс в формате *22.88*',
                           chat_id=callback.from_user.id,
                           parse_mode='Markdown')
    await state.set_state(RateState.rate)


@dp.message(RateState.rate)
async def process_rate(message: types.Message, state: FSMContext) -> None:
    try:
        new_rate = float(message.text)
        global YUAN_RATE
        YUAN_RATE = new_rate
        funcs.update_yuan_rate(new_rate)
        await bot.send_message(chat_id=message.chat.id, text='Курс юаня успешно обновлен!')
        await state.clear()
    except:
        await bot.send_message(chat_id=message.chat.id, text='Произошла ошибка при установке курса юаня, попробуй '
                                                             'установить курс еще раз!')
        await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
