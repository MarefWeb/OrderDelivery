from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

work_type_kb = InlineKeyboardMarkup().row(InlineKeyboardButton('Телеграм бот', callback_data='work_type_bot'),
                                          InlineKeyboardButton('Сайт', callback_data='work_type_site'))

order_answer_kb = InlineKeyboardMarkup().row(InlineKeyboardButton('Принять', callback_data='order_answer_accept'),
                                             InlineKeyboardButton('Отклонить', callback_data='order_answer_dismiss'))
