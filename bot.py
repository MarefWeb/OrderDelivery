from aiogram import Bot, Dispatcher, executor, types
from config import TOKEN, DB_NAME, Step, CHAT_OUTPUT, CREDENTIALS_FILE, SPREAD_SHEET_ID
from keyboard import work_type_kb, order_answer_kb
from sqlite import SQLighter
from oauth2client.service_account import ServiceAccountCredentials
import requests
import os
import random
import httplib2
import googleapiclient.discovery

bot = Bot(TOKEN)
dp = Dispatcher(bot)

db = SQLighter(DB_NAME)


async def add_client(message, chat_id, username):
    db.add_client(chat_id=chat_id, username=username)
    await message.answer('Здравствуйте. Какой вид услуг вас интересует?', reply_markup=work_type_kb)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if 'username' in message.from_user:
        chat_id = message.from_user.id
        username = '@' + message.from_user.username
        step_list = db.get_step(username)

        if step_list is None:
            await add_client(message=message, chat_id=chat_id, username=username)

        else:
            step = step_list[0]

            if step == Step.CHOOSE_WORK_TYPE.value:
                await message.answer('Сейчас вы находитесь на этапе выбора типа работы.\n'
                                     'Так какой вид услуг вас интересует?', reply_markup=work_type_kb)

            elif step == Step.ENTER_BUDGET.value:
                await message.answer('Сейчас вы находитесь на этапе ввода бюджета проекта.\n'
                                     'Если бюджет по нашему усмотрению, то введите "-".\n'
                                     'Или сумму, на которуюв ы расчитываете? (в рублях)')

            elif step == Step.SEND_TASK_FILE.value:
                await message.answer('Сейчас вы находитесь на этапе отправки технического задания.\n'
                                     'Отправьте файл, в котором будет описана цель работы и ваши предпочтения:')

            elif step == Step.COMPLETE.value:
                db.reset_data(username=username)
                await message.answer('Давно не виделись. Какой вид услуг вас интересует сейчас?',
                                     reply_markup=work_type_kb)

            else:
                await add_client(message=message, chat_id=chat_id, username=username)

    else:
        await message.answer('Извините, у вас отсутствует логин. Добавьте логин и возвращайтесь к нам!')


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    username = '@' + message.from_user.username

    db.reset_data(username)
    await message.answer('Хорошо, начнём сначала. Что вы хотите заказать?', reply_markup=work_type_kb)


def check_work_type_readiness(callback):
    if callback.data == 'work_type_bot' or callback.data == 'work_type_site':
        username = '@' + callback.from_user.username
        return db.get_step(username)[0] == Step.CHOOSE_WORK_TYPE.value
    else:
        return False


@dp.callback_query_handler(lambda callback: check_work_type_readiness(callback))
async def work_type(callback_query: types.CallbackQuery):
    username = '@' + callback_query.from_user.username

    if callback_query.data == 'work_type_bot':
        db.update_work_type(username, 'телеграм бот')
    elif callback_query.data == 'work_type_site':
        db.update_work_type(username, 'сайт')

    db.update_step(username=username, step=Step.ENTER_BUDGET.value)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Хорошо, теперь определим бюджет проекта.\n'
                                                        'Если на наше усмотрение, то введите "-".\n'
                                                        'Или же введите сумму на которую расчитываете (в рублях):')


@dp.message_handler(lambda message: db.get_step('@' + message.from_user.username)[0] == Step.ENTER_BUDGET.value)
async def enter_budget(message: types.Message):
    username = '@' + message.from_user.username
    budget = message.text

    if not budget.isdigit() and budget != '-':
        await message.answer('Что-то пошло не так, попробуйте ещё раз!')

    else:
        if budget == '-':
            db.update_budget(username=username, budget='на ваше усмотрение')
        else:
            db.update_budget(username=username, budget=budget + 'р')

        db.update_step(username=username, step=Step.SEND_TASK_FILE.value)
        await message.answer('Отлично, теперь отправьте файл с техническим заданием:')


@dp.message_handler(lambda m: db.get_step('@' + m.from_user.username)[0] == Step.SEND_TASK_FILE.value,
                    content_types=types.ContentType.DOCUMENT)
async def send_photo(message: types.Message):
    username = '@' + message.from_user.username

    doc_id = message.document.file_id
    file_info = await bot.get_file(doc_id)
    file_path = file_info.file_path
    file_name = message.document.file_name
    r = requests.get(f'https://api.telegram.org/file/bot{TOKEN}/{file_path}')

    while file_name in os.listdir('Tasks'):
        file_name = file_name.split('.')
        file_name[0] = file_name[0] + str(random.randrange(100))
        file_name = '.'.join(file_name)

    with open(f'Tasks/{file_name}', 'wb') as f:
        f.write(r.content)

    db.update_task_file(username=username, task_file=file_name)
    db.update_step(username=username, step=Step.COMPLETE.value)
    await message.answer('Спасибо за ваш заказ.\nВ скором времени мы с вами свяжемся.')

    client_info = db.get_client_data(username)
    client_username = client_info[2]
    client_work_type = client_info[3]
    client_budget = client_info[4]
    client_task_file = open('Tasks\\' + client_info[5], 'rb')

    await bot.send_document(chat_id=CHAT_OUTPUT, document=client_task_file, caption=f'Техническое задание👆👆👆\n'
                                                                                    f'Ссылка на пользователя:'
                                                                                    f'  {client_username}\nТип работы: '
                                                                                    f' {client_work_type}\n'
                                                                                    f'Бюджет проекта:  {client_budget}',
                            reply_markup=order_answer_kb)


@dp.callback_query_handler(lambda callback: str(callback.message.chat.id) == CHAT_OUTPUT)
async def order_answer(callback_query: types.CallbackQuery):
    client_username = callback_query.message.caption.split('\n')[1].split(':  ')[1]
    client_chat_id = db.get_client_data(client_username)[1]
    order_status = db.get_order_status(client_username)[0]

    if callback_query.data == 'order_answer_accept':
        if order_status == 1:
            await bot.answer_callback_query(callback_query_id=callback_query.id,
                                            text='Заказ уже принят!')
            return
        else:
            client_work_type = db.get_client_data(client_username)[3]
            client_budget = db.get_client_data(client_username)[4]
            client_task_file = db.get_client_data(client_username)[5]

            spreadsheets_data = [client_username, client_work_type, client_budget, client_task_file]

            credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'])
            http_auth = credentials.authorize(httplib2.Http())
            service = googleapiclient.discovery.build('sheets', 'v4', http=http_auth)

            busy = True
            cell_number = 1

            while busy:
                ranges = [f'заказы!A{cell_number}:d{cell_number}']

                result = service.spreadsheets().values().batchGet(spreadsheetId=SPREAD_SHEET_ID,
                                                                  ranges=ranges,
                                                                  valueRenderOption='FORMATTED_VALUE',
                                                                  dateTimeRenderOption='FORMATTED_STRING').execute()

                if 'values' in result['valueRanges'][0]:
                    cell_number += 1

                else:
                    ranges = f'заказы!A{cell_number}:D{cell_number}'

                    service.spreadsheets().values().batchUpdate(spreadsheetId=SPREAD_SHEET_ID,
                                                                body={
                                                                    'valueInputOption': 'USER_ENTERED',
                                                                    'data': [
                                                                        {
                                                                            'range': ranges,
                                                                            'majorDimension': 'ROWS',
                                                                            'values': [
                                                                                spreadsheets_data
                                                                            ]
                                                                        }
                                                                    ]
                                                                }).execute()

                    busy = False

            db.active_order(client_username)
            await bot.send_message(client_chat_id, 'Ваш заказ принят. В скором времени мы с вами свяжемся!')

    elif callback_query.data == 'order_answer_dismiss':
        if order_status == 1:
            await bot.answer_callback_query(callback_query_id=callback_query.id,
                                            text='Не возможно отказаться, вы уже приняли этот заказ!')
            return
        else:
            db.reset_data(client_username)
            await callback_query.message.delete()
            await bot.send_message(client_chat_id, 'Ваш заказ отклонён.')

    await bot.answer_callback_query(callback_query.id)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp)
