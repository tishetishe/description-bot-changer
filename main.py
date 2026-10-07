import logging
import asyncio
import random
import redis.asyncio as redis
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart , Command , CommandObject
from keyboard_panel import keyboardpanel
from dotenv import load_dotenv
import os


load_dotenv("secret.env")


API_TOKEN = os.getenv("API_TOKEN") #токен вашего бота
CHANNEL_ID = os.getenv("CHANNEL_ID") #ваш канал/группа
ADMIN_ID = int(os.getenv("ADMIN_ID")) #айди админа(вообще есть автоматическая функция , ну да ладно)


r = redis.from_url("redis://localhost:6379/0" , decode_responses=True) #декодируем байты в строки
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


PHRASES_KEY="sen:description" #список фраз в так называемой папке чтобы не перезаписывались
TIMER_KEY = "sen:interval" #список времени



@dp.message(CommandStart())
async def send_welcome(message: Message):
        await message.answer("Добро пожаловать.\nЭтот бот создан для изменения описания в вашем канале по временному интервалу.\nНапишите команду /help что бы узнать список команд\nИ не забудьте указать время смены описаний❗️" , reply_markup=keyboardpanel())



@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("/setime — установить время смены описаний\n/addesc — добавить описание\n/deldesc — удалить описание по определенному номеру")




@dp.message(Command("addesc") , F.from_user.id == ADMIN_ID)
async def add_desc(message: Message , command: CommandObject):
 
    text = command.args #удаляет пробелы в начале и в конце и выводит только текст(без команды)
    
    if not text:
        return await message.reply("❌Введите правильно описание.Например: /addesc <описание>")

    await r.rpush(PHRASES_KEY , text) #добавляет в конце списка памяти рЕдис
    await r.persist(PHRASES_KEY) #гарантирует что LLT бесконечный будет
    await message.answer("Описание успешно добавлено✅")




@dp.message(F.text == "🗒Вывод всех описаний" , F.from_user.id == ADMIN_ID)
async def list_desc(message: Message):
    
    descs = await r.lrange(PHRASES_KEY , 0 , -1) #вывод от начала до конца списка
    if not descs:
        return await message.reply("Ваш список пуст")
    text = "\n".join(f"{i+1}. {d}" for i , d in enumerate(descs))
    await message.answer(text)





@dp.message(F.text == "❌Удалить последнее описание", F.from_user.id == ADMIN_ID)
async def del_decsriprion(message: Message):
    
    descs = await r.rpop(PHRASES_KEY)
    if not descs:
        return await message.reply("Ваш список на данный момент пуст")
    await message.answer("⚠️Ваше последние описание удалено")




@dp.message(F.text == "🗑Удалить все описания", F.from_user.id == ADMIN_ID)
async def del_all_decsriprion(message: Message):

    descs = await r.delete(PHRASES_KEY)
    if not descs:
        return await message.reply("Ваш список на данный момент итак пуст") 
    await message.answer("⚠️Ваш список полностью удален")




@dp.message(Command("deldesc") , F.from_user.id == ADMIN_ID)
async def enumerate_del_cmd(message: Message , command: CommandObject):

    arg = command.args

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




@dp.message(Command("setime"), F.from_user.id == ADMIN_ID)
async def set_time(message: Message):
    
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



 #return await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")


async def route_descriptions():
    while True:
        interval = int(await r.get(TIMER_KEY) or 6 * 60 * 60)
        descs = await r.lrange(PHRASES_KEY , 0 , -1)

        if not descs:
            await asyncio.sleep(3600)
            continue

        desc = random.choice(descs)

        try:
            await bot.set_chat_description(chat_id=CHANNEL_ID, description=desc) #меняем описание
        except Exception as e:
            print(f"Error updating channel description: {e}")
        await asyncio.sleep(interval) #Временной интервал



async def main():
    asyncio.create_task(route_descriptions())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())