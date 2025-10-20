import logging
import asyncio
import random
import redis.asyncio as redis
from aiogram import Bot, Dispatcher, types , executor
from aiogram import types
from aiogram.dispatcher.filters import Command
from keyboard_panel import keyboardpanel
from dotenv import load_dotenv
import os


load_dotenv("secret.env")


API_TOKEN = os.getenv("API_TOKEN") #токен вашего бота
CHANNEL_ID = os.getenv("CHANNEL_ID") #ваш канал/группа
ADMIN_ID = int(os.getenv("ADMIN_ID")) #айди админа(вообще есть автоматическая функция , ну да ладно)


r = redis.from_url("redis://localhost:6379/0" , decode_responses=True)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


PHRASES_KEY="sen:description" #список фраз
TIMER_KEY = "sen:interval" #список временни



async def is_admin(user_id: int , chat_id: str):
    admins = await bot.get_chat_administrators(chat_id) #получаем айди админа группы
    return any(admin.user.id == user_id for admin in admins) #находим всех админов




@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
        await message.answer("Добро пожаловать.\nЭтот бот создан для изменения описания в вашем канале по временному интервалу.\nНапишите команду /help что бы узнать список команд\nИ не забудьте указать время смены описаний❗️" , reply_markup=keyboardpanel())



@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("/setime — установить время смены описаний\n/addesc — добавить описание\n/deldesc — удалить описание по определенному номеру")




@dp.message_handler(commands=['addesc'])
async def add_desc(message: types.Message):
    if not await is_admin(message.from_user.id , CHANNEL_ID):
        return await message.reply("У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")

    text = message.get_args().strip() #удаляет пробелы в начале и в конце и выводит только текст(без команды)

    if not text:
        return message.reply("❌Введите правильно описание.Например: /addesc <описание>")

    await r.rpush(PHRASES_KEY , text) #добавляет в конце списка памяти рЕдис
    await r.persist(PHRASES_KEY) #гарантирует что LLT бесконечный будет
    await message.answer("Описание успешно добавлено✅")




@dp.message_handler(lambda message: message.text == "🗒Вывод всех описаний")
async def list_desc(message: types.Message):
    if not await is_admin(message.from_user.id , CHANNEL_ID):
       return await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")

    descs = await r.lrange(PHRASES_KEY , 0 , -1) #вывод от начала до конца списка
    if not descs:
        return await message.reply("Ваш список пуст")
    text = "\n".join(f"{i+1}. {d}" for i , d in enumerate(descs))
    await message.answer(text)





@dp.message_handler(lambda message: message.text == "❌Удалить последнее описание")
async def del_decsriprion(message: types.Message):
    if not await is_admin(message.from_user.id , CHANNEL_ID):
       return await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")

    descs = await r.rpop(PHRASES_KEY)
    if not descs:
        return await message.reply("Ваш список на данный момент пуст")
    await message.answer("⚠️Ваше последние описание удалено")




@dp.message_handler(lambda message: message.text == "🗑Удалить все описания")
async def del_all_decsriprion(message: types.Message):
    if not await is_admin(message.from_user.id , CHANNEL_ID):
       return await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")

    descs = await r.delete(PHRASES_KEY)
    if not descs:
        return await message.reply("Ваш список на данный момент итак пуст") 
    await message.answer("⚠️Ваш список полностью удален")




@dp.message_handler(commands=['deldesc'])
async def enumerate_del_cmd(message: types.Message):
    if not await is_admin(message.from_user.id , CHANNEL_ID):
        return await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")

    arg = message.get_args().strip()

    if not arg.isdigit():
        return await message.reply("❌Вы ввели команду неверно.\n Введите корректно команду , например: /deldesc <номер>")

    index = int(arg) - 1 #что бы не шло с 0, а еденицы 

    descs = await r.lrange(PHRASES_KEY , 0 , -1) #вывод от начала до конца списка
    if not descs:
        return await message.reply("❌Ваш список пуст")
    if index < 0 or index > len(descs):
        return await message.reply("❌У вас нет описания с таким номером")

    removed = descs[index] #запоменаем удаленный номер

    await r.lset(PHRASES_KEY , index , "__TO_DELETE__") #заменяем описание на метку
    await r.lrem(PHRASES_KEY , 0 , "__TO_DELETE__") #удаляем все элементы с этой меткой

    await message.reply(f"⚠️Удалено описание с номером {index+1}:\n{removed}")




@dp.message_handler(commands=['setime'])
async def set_time(message: types.Message):
    if not await is_admin(message.from_user.id , CHANNEL_ID):
       return await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")

    descs = await r.lrange(PHRASES_KEY , 0 , -1) #получаем список от начала до конца
    if not descs:
        return await message.reply("❌Ваш список пуст")

    arg = message.get_args().strip().lower() #возвращает то что написано после команды 

    if not arg:
        return await message.answer("❌Введите правильный формат: /setime 6h(или 30m, 1h, 10s)")

    multipliers = {"s" : 1, "m" : 60 , "h": 3600} #таблица перевода в секунды по ключевому значению

    try:
        value = int(float(arg[:-1] or arg) * {"s" : 1, "m" : 60 , "h": 3600}.get(arg[-1], 1))
    except (ValueError, KeyError):
        return await message.reply("❌Неверный формат.Введите правильный формат: /setime 6h(или 30m, 1h, 10s)")

    await r.set(TIMER_KEY, value)
    await message.reply(f"⚠️Время смены описаний: {arg}")




async def route_descriptions():
    while True:
        interval = int(await r.get(TIMER_KEY) or 6 * 60 * 60) #время по девофлту стоит 6 часов!
        descs = await r.rpoplpush(PHRASES_KEY , PHRASES_KEY) #перемещается с конца в начало списка
        if not descs:
            await asyncio.sleep(3600) #проверка изменений через час
            continue
        try:
            await bot.set_chat_description(chat_id=CHANNEL_ID, description=descs) #меняем описание
        except Exception as e:
            print(f"Error updating channel description: {e}")
        await asyncio.sleep(interval) #Временной интервал



async def on_startup(_):
    asyncio.create_task(route_descriptions())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True , on_startup=on_startup)