from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yaml
with open("source/texts.yaml", "r", encoding="utf-8") as file:
    text = yaml.safe_load(file)

def main_keyboard(chat_id: int) -> InlineKeyboardMarkup:

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

    if chat_id == 455153917:
        builder.row(
            InlineKeyboardButton(
                text=f'Установить курс юаня', callback_data='set_rate',
            )
        )

    return builder.as_markup()

def categories_keyboard(categories:dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for id, cat in categories.items():
        builder.row(
            InlineKeyboardButton(
                text=cat['category'],
                callback_data=id
            )
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
        InlineKeyboardButton(text='Оформить заказ', url='https://rutube.ru/video/c6cc4d620b1d4338901770a44b3e82f4/'),
    )
    builder.row(
        InlineKeyboardButton(text='Рассчитать еще', callback_data='calculate'),
    )
    return builder.as_markup()