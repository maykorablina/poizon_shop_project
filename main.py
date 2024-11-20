import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from source import keyboards as kb
import yaml
from dotenv import load_dotenv
from aiogram import F
import os
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ContentType, ChatMemberStatus
from aiogram.fsm.context import FSMContext
from source import functions as funcs

load_dotenv()
global YUAN_RATE
YUAN_RATE = float(os.getenv('YUAN_RATE'))
TOKEN_API = os.getenv('TOKEN_API')
tariffs = funcs.load_tariffs()
ADMIN_ID = int(os.getenv('ADMIN_ID'))
DEV_ID = int(os.getenv('DEV_ID'))
MANAGER_ID = int(os.getenv('MANAGER_ID'))

bot = Bot(TOKEN_API)
dp = Dispatcher()
with open("source/texts.yaml", "r", encoding="utf-8") as file:
    text = yaml.safe_load(file)


async def is_user_subscribed(channel_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

@dp.message(Command("start"))
async def beginning(message):
    chat_id = message.chat.id

    if not await is_user_subscribed(text['subscribe']['channel_name'], chat_id):
        await bot.send_message(chat_id=chat_id, text=text['subscribe']['please_subscribe'],
                               reply_markup=kb.subscribe_to_channel(), parse_mode='Markdown')
    else:
        await bot.send_message(chat_id=chat_id, text=text['menu']['message'],
                               reply_markup=kb.main_keyboard(chat_id=chat_id, admins=[ADMIN_ID, DEV_ID]),
                               parse_mode='Markdown')


@dp.callback_query(F.data.startswith('check_subscribe'))
async def check_subscribe(callback: types.CallbackQuery):
    if await is_user_subscribed(text['subscribe']['channel_name'], callback.from_user.id):
        await bot.send_message(chat_id=callback.from_user.id, text=text['subscribe']['check_success'], )
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.from_user.id)
    else:
        await callback.answer(text=text['subscribe']['check_failure'])


class Calculator(StatesGroup):
    price_yuan = State()
    category = State()
    del_way = State()
    order = State()


@dp.callback_query(F.data.startswith('calculate'))
async def begin_calculation(callback: types.CallbackQuery, state: FSMContext):
    if not await is_user_subscribed(text['subscribe']['channel_name'], callback.from_user.id):
        await bot.send_message(chat_id=callback.from_user.id, text=text['subscribe']['please_subscribe'],
                               reply_markup=kb.subscribe_to_channel(), parse_mode='Markdown')
        await state.clear()
    else:
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
                               reply_markup=kb.categories_keyboard(tariffs['tariffs'], 0, type='calc'),
                               parse_mode='Markdown'
                               )
    except Exception as e:
        print(e)
        await bot.send_message(chat_id=message.chat.id,
                               text=text["calculator"]["enter_price_error"],
                               parse_mode='Markdown'
                               )
        await state.clear()

@dp.callback_query(F.data.startswith('calc_cat_next'))
async def cat_page_next_calc(callback: types.CallbackQuery, state: FSMContext):
    pg = int(callback.data.split(' ')[1])
    await callback.message.edit_text(text=text["calculator"]["choose_category"],reply_markup=kb.categories_keyboard(tariffs['tariffs'], pg, type='calc'))
    await state.set_state(Calculator.category)

@dp.callback_query(F.data.startswith('edit_cat_next'))
async def cat_page_next_calc(callback: types.CallbackQuery, state: FSMContext):
    pg = int(callback.data.split(' ')[1])
    await callback.message.edit_text(text="Выбери категорию",reply_markup=kb.categories_keyboard(tariffs['tariffs'], pg, type='edit'))
    await state.set_state(Calculator.category)

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
        "del_avia_duration": '-'.join(funcs.calc_date(tariffs['delivery_time']['avia'])),
        "del_auto_price": category_info['auto'],
        "del_auto_duration": '-'.join(funcs.calc_date(tariffs['delivery_time']['avia'])),
        "price_with_comissions": round(data['price_yuan'] * YUAN_RATE * 1.08 * (1 if data['price_yuan'] < 1500 else 1.03), 2)
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
        "final_price": round(data['price_yuan'] * YUAN_RATE * (1 if data['price_yuan'] < 1500 else 1.03) * 1.08 +
                       category_info[data['del_way']], 2),
    }

    await bot.send_message(chat_id=callback.from_user.id, text=text["calculator"]["final_price"].format(**order_info),
                           reply_markup=kb.calculator_last_keyboard(),
                           parse_mode='Markdown')
    await state.set_state(Calculator.order)


@dp.callback_query(Calculator.order)
async def set_delivery(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.startswith('make_order'):
        data = await state.get_data()
        category_info = tariffs['tariffs'][data['category']]
        order_info = {
            "category": category_info['category'],
            "price_yuan": data['price_yuan'],
            "price_rub": data['price_yuan'] * YUAN_RATE,
            "del_way": data['del_way'],
            "final_price": round(data['price_yuan'] * YUAN_RATE * (1 if data['price_yuan'] < 1500 else 1.03) * 1.08 +
                                 category_info[data['del_way']], 2),
            "user_tag": f'@{callback.from_user.username}',
        }
        await bot.send_message(chat_id=callback.from_user.id, text=text["calculator"]["thanks_for_order"],
                               parse_mode='Markdown')
        await bot.send_message(chat_id=ADMIN_ID,text=text["calculator"]["order_info_message"].format(**order_info),
                               parse_mode='Markdown')
        await bot.send_message(chat_id=MANAGER_ID, text=text["calculator"]["order_info_message"].format(**order_info),
                               parse_mode='Markdown')
        await state.clear()



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

class EditCats(StatesGroup):
    cat_id = State()

@dp.callback_query(F.data.startswith('edit_categories'))
async def edit_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(EditCats.cat_id)
    await bot.send_message(chat_id=callback.from_user.id, text="Выбери категорию", reply_markup=kb.categories_keyboard(tariffs['tariffs'], 0, type='edit'))


@dp.callback_query(F.data.startswith('edit_categories'))
async def edit_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(EditCats.cat_id)
    await bot.send_message(chat_id=callback.from_user.id, text="Выбери категорию",
                           reply_markup=kb.categories_keyboard(tariffs['tariffs'], 0, type='edit'))


@dp.callback_query(F.data.startswith('edit_categories'))
async def edit_categories(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(EditCats.cat_id)
    await bot.send_message(chat_id=callback.from_user.id, text="Выбери категорию",
                           reply_markup=kb.categories_keyboard(tariffs['tariffs'], 0, type='edit'))


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
