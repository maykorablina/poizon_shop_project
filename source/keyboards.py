from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yaml
with open("source/texts.yaml", "r", encoding="utf-8") as file:
    text = yaml.safe_load(file)

def back_menu_keyboard():
    kb_list = [
        [KeyboardButton(text="Вернуться в меню")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=False)
    return keyboard

def main_keyboard(chat_id: int, admins: list[int]) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=text['menu']['faq'], url=text['menu']['faq_link']
        ),
        InlineKeyboardButton(
            text=text['menu']['wiki'], url=text['menu']['wiki_link']
        ),
        InlineKeyboardButton(
            text=text['menu']['reviews'], url=text['menu']['reviews_link']
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=text['menu']['manager'], url=text['menu']['manager_link']
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=text['menu']['calculator'], callback_data='calculate'
        )
    )

    if chat_id in admins:
        builder.row(
            InlineKeyboardButton(
                text=f'Установить курс юаня', callback_data='set_rate',
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=f'Редактировать категории', callback_data='edit_categories',
            )
        )

    return builder.as_markup()

def categories_keyboard(categories:dict, cat_start:int, type:str) -> InlineKeyboardMarkup:
    cat_items = list(categories.items())[cat_start:cat_start+4]
    if type == 'edit':
        cat_items.insert(0, ("new_cat", {'category':"Создать категорию"}))
    builder = InlineKeyboardBuilder()
    for id, cat in cat_items:
        builder.row(
            InlineKeyboardButton(
                text=cat['category'],
                callback_data=id
            )
        )
    if cat_start == 0:
        builder.row(
            InlineKeyboardButton(text='>>>', callback_data=f'{type}_cat_next {cat_start+4}'),
        )
    elif cat_start+5 > len(categories):
        builder.row(
            InlineKeyboardButton(text='<<<', callback_data=f'{type}_cat_next {cat_start-4}'),
        )
    else:
        builder.row(
            InlineKeyboardButton(text='<<<', callback_data=f'{type}_cat_next {cat_start -4}'),
            InlineKeyboardButton(text='>>>', callback_data=f'{type}_cat_next {cat_start + 4}'),
        )


    return builder.as_markup()

def del_type_keyboard(categories:dict, cat_id) -> InlineKeyboardMarkup:
    cats = categories.copy()
    builder = InlineKeyboardBuilder()
    category = list(categories[cat_id].items())[1:]
    print(category)
    bts = []
    for k, v in category:
        if v:
            bts.append(
                InlineKeyboardButton(
                    text=("Авиа" if k == 'avia' else "Авто"),
                    callback_data=k
                )
            )
    builder.row(*bts)

    return builder.as_markup()

def calculator_last_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=text['calculator']['make_order'], callback_data='make_order'),
    )
    builder.row(
        InlineKeyboardButton(text=text['calculator']['calc_again'], callback_data='calculate'),
    )
    return builder.as_markup()

def subscribe_to_channel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=text['subscribe']['subscribe_button'], url=text['subscribe']['subscribe_link']),
    )
    builder.row(
        InlineKeyboardButton(text=text['subscribe']['check_button'], callback_data='check_subscribe'),
    )
    return builder.as_markup()

def what_to_edit() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Название категории", callback_data='category'),
    )
    builder.row(
        InlineKeyboardButton(text="Стоимость авто", callback_data='auto'),
    )
    builder.row(
        InlineKeyboardButton(text="Стоимость авиа", callback_data='avia'),
    )
    builder.row(
        InlineKeyboardButton(text="Удалить категорию", callback_data='delete_category'),
    )
    return builder.as_markup()