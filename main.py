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
global tariffs
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
async def beginning(message, state: FSMContext):
    await state.clear()
    chat_id = message.chat.id

    if not await is_user_subscribed(text['subscribe']['channel_name'], chat_id):
        await bot.send_message(chat_id=chat_id, text=text['subscribe']['please_subscribe'],
                               reply_markup=kb.subscribe_to_channel(), parse_mode='Markdown')
    else:
        await bot.send_message(chat_id=chat_id, text=text['menu']['message'],
                               reply_markup=kb.main_keyboard(chat_id=chat_id, admins=[ADMIN_ID]),
                               parse_mode='Markdown')

@dp.message(Command("menu"))
async def menu(message, state: FSMContext):
    await state.clear()
    await bot.send_message(chat_id=message.chat.id, text=text['menu']['message'],
                           reply_markup=kb.main_keyboard(chat_id=message.chat.id, admins=[ADMIN_ID]),
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
        await bot.send_message(chat_id=message.chat.id,
                               text=text["calculator"]["enter_price_error"],
                               parse_mode='Markdown'
                               )
        await state.clear()


@dp.callback_query(F.data.startswith('calc_cat_next'), Calculator.category)
async def cat_page_next_calc(callback: types.CallbackQuery, state: FSMContext):
    pg = int(callback.data.split(' ')[1])
    await callback.message.edit_text(text=text["calculator"]["choose_category"],
                                     reply_markup=kb.categories_keyboard(tariffs['tariffs'], pg, type='calc'))
    await state.set_state(Calculator.category)


@dp.callback_query(Calculator.category)
async def set_delivery(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data)
    print(callback.data)
    cat_id = callback.data
    data = await state.get_data()
    category_info = tariffs['tariffs'][cat_id]
    avia_flag = True
    auto_flag = True
    if not category_info['avia']:
        avia_flag = False
    if not category_info['auto']:
        auto_flag = False
    print(data)
    product_info = {
        "price_yuan": int(data['price_yuan']),
        "price_rub": funcs.screen(int(data['price_yuan'] * YUAN_RATE)),
        "del_avia_price": funcs.screen(
            (category_info['avia'] if avia_flag else text['calculator']['no_delivery'])
        ),
        "del_avia_duration": funcs.screen(
            ('-'.join(funcs.calc_date(tariffs['delivery_time']['avia'])) if avia_flag else '')
        ),
        "del_auto_price": funcs.screen(
            (category_info['auto'] if auto_flag else text['calculator']['no_delivery'])
        ),
        "del_auto_duration": funcs.screen(
            ('-'.join(funcs.calc_date(tariffs['delivery_time']['auto'])) if auto_flag else '')
        ),
        "price_with_comissions": int(funcs.round_to_50(
            data['price_yuan'] * YUAN_RATE * 1.08 * (1 if data['price_yuan'] < 1500 else 1.03)))
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
        "category": funcs.screen(category_info['category']),
        "price_yuan": int(data['price_yuan']),
        "price_rub": int(data['price_yuan'] * YUAN_RATE),
        "del_way": ("Авто" if data['del_way'] == 'auto' else "Авиа"),
        "final_price": int(funcs.round_to_50(
            data['price_yuan'] * YUAN_RATE * (1 if data['price_yuan'] < 1500 else 1.03) * 1.08 +
            category_info[data['del_way']])),
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
            "category": funcs.screen(category_info['category']),
            "price_yuan": int(data['price_yuan']),
            "price_rub": int(data['price_yuan'] * YUAN_RATE),
            "del_way": ("Авто" if data['del_way'] == 'auto' else "Авиа"),
            "final_price": int(funcs.round_to_50(
                data['price_yuan'] * YUAN_RATE * (1 if data['price_yuan'] < 1500 else 1.03) * 1.08 +
                category_info[data['del_way']])),
            "user_tag": funcs.screen(f'@{callback.from_user.username}'),
        }
        await bot.send_message(chat_id=callback.from_user.id, text=text["calculator"]["thanks_for_order"],
                               parse_mode='Markdown')
        await bot.send_message(chat_id=ADMIN_ID, text=text["calculator"]["order_info_message"].format(**order_info),
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


@dp.callback_query(F.data.startswith('edit_cat_next'))
async def cat_page_next_calc(callback: types.CallbackQuery, state: FSMContext):
    pg = int(callback.data.split(' ')[1])
    await callback.message.edit_text(text="Выбери категорию",
                                     reply_markup=kb.categories_keyboard(tariffs['tariffs'], pg, type='edit'))
    await state.set_state(EditCats.cat_id)


class EditCats(StatesGroup):
    cat_id = State()
    cat_change_data = State()
    edit = State()


@dp.callback_query(F.data.startswith('edit_categories'))
async def edit_categories(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=callback.from_user.id, text="Выбери категорию",
                           reply_markup=kb.categories_keyboard(tariffs['tariffs'], 0, type='edit'))
    await state.set_state(EditCats.cat_id)


class CreateCat(StatesGroup):
    cat_name = State()
    cat_price_avia = State()
    cat_price_auto = State()


@dp.callback_query(F.data.startswith('new_cat'))
async def new_cat(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_message(chat_id=callback.from_user.id, text="Введи название категории")
    await state.set_state(CreateCat.cat_name)


@dp.message(CreateCat.cat_name)
async def set_name(message: types.Message, state: FSMContext):
    await state.update_data(cat_name=message.text)
    await bot.send_message(chat_id=message.chat.id,
                           text="Введи стоимость доставки *авто* в формате *20.15*\nЕсли такой способ доставки отсутствует, введи *0*",
                           parse_mode='Markdown')
    await state.set_state(CreateCat.cat_price_auto)


@dp.message(CreateCat.cat_price_auto)
async def set_name(message: types.Message, state: FSMContext):
    try:
        await state.update_data(cat_price_auto=int(message.text))
        await bot.send_message(chat_id=message.chat.id,
                               text="Введи стоимость доставки *авиа* в формате *20.15*\nЕсли такой способ доставки отсутствует, введи *0*",
                               parse_mode='Markdown')
        await state.set_state(CreateCat.cat_price_avia)
    except:
        await bot.send_message(chat_id=message.chat.id,
                               text="*При вводе стоимости произошла ошибка*\n\nЕще раз введи стоимость доставки *авто* в формате *20.15*\nЕсли такой способ доставки отсутствует, введи *0*",
                               parse_mode='Markdown')
        await state.set_state(CreateCat.cat_price_auto)


@dp.message(CreateCat.cat_price_avia)
async def set_name(message: types.Message, state: FSMContext):
    try:
        await state.update_data(cat_price_avia=int(message.text))
        data = await state.get_data()
        id = str(len(tariffs['tariffs']) + 1)
        tariffs['tariffs'][id] = {'category': data['cat_name'], 'avia': data['cat_price_avia'],
                                  'auto': data['cat_price_auto']}
        funcs.save_tariffs(tariffs)
        await bot.send_message(chat_id=message.chat.id,
                               text=f'Категория *"{funcs.screen(data['cat_name'])}"* успешно создана!\nЦена *авто*: {data["cat_price_auto"]}\nЦена *авиа*: {data["cat_price_avia"]}',
                               parse_mode='Markdown')
    except:
        await bot.send_message(chat_id=message.chat.id,
                               text="*При вводе стоимости произошла ошибка*\n\nЕще раз введи стоимость доставки "
                                    "*авто* в формате *20.15*\nЕсли такой способ доставки отсутствует, введи *0*",
                               parse_mode="Markdown")
        await state.set_state(CreateCat.cat_price_avia)


@dp.callback_query(EditCats.cat_id)
async def choose_to_edit(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data
    await state.update_data(cat_id=callback.data)
    category = tariffs['tariffs'][callback.data]
    txt = f"Категория: {funcs.screen(category['category'])}\nСтоимость *авто*: {category['auto']} руб.\nСтоимость *авиа*: {category['avia']} руб.*\n\n*Что нужно поменять?"
    await bot.send_message(chat_id=callback.from_user.id, text=txt, reply_markup=kb.what_to_edit(),
                           parse_mode="Markdown")
    await state.set_state(EditCats.cat_change_data)


@dp.callback_query(F.data.startswith('delete_category'), EditCats.cat_change_data)
async def edit_categories(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    del tariffs['tariffs'][data['cat_id']]
    funcs.save_tariffs(tariffs)
    await bot.send_message(chat_id=callback.from_user.id, text="Категория успешно удалена!")
    await state.clear()


@dp.callback_query(EditCats.cat_change_data)
async def edit(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cat_change_data=callback.data)
    t = ''
    if callback.data == 'category':
        t = "категории товара"
    elif callback.data == 'auto':
        t = "цены доставки *авто*"
    elif callback.data == 'avia':
        t = "цены доставки *авиа*"
    await bot.send_message(chat_id=callback.from_user.id,
                           text=f"Введи новое значение для {t}{(' в формате *20.15*' if callback.data != 'category' else '')}{('\n\nЕсли хочешь убрать этот способ доставки, введи * 0 *') if callback.data in ['auto', 'avia'] else ''}",
                           parse_mode="Markdown")
    await state.set_state(EditCats.edit)


@dp.message(EditCats.edit)
async def set_new(message: types.Message, state: FSMContext):
    await state.update_data(edit=message.text)
    data = await state.get_data()
    new_value = data['edit']
    if data['cat_change_data'] != 'category':
        if new_value == '0':
            new_value = None
        else:
            new_value = int(new_value)
    tariffs['tariffs'][data['cat_id']][data['cat_change_data']] = new_value
    t = ''
    funcs.save_tariffs(tariffs)
    if data['cat_change_data'] == 'category':
        t = "Название категории товара"
    elif data['cat_change_data'] == 'auto':
        t = "Цена доставки *авто*"
    elif data['cat_change_data'] == 'avia':
        t = "Цена доставки *авиа*"
    txt = f'{t} успешно изменен{('о' if data['cat_change_data'] == 'category' else 'a')}!'
    await bot.send_message(chat_id=message.chat.id, text=txt, parse_mode="Markdown")
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
