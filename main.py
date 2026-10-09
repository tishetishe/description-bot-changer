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
logging.basicConfig(level=logging.INFO)


API_TOKEN = os.getenv("API_TOKEN") #токен вашего бота
CHANNEL_ID = os.getenv("CHANNEL_ID") #ваш канал/группа(указывать в env через @ вместо t.me!)
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
    await r.persist(PHRASES_KEY) #гарантирует что LLT(время жизни) бесконечный будет
    await message.answer("Описание успешно добавлено✅")




@dp.message(F.text == "🗒Вывод всех описаний" , F.from_user.id == ADMIN_ID)
async def list_desc(message: Message):
    
    descs = await r.lrange(PHRASES_KEY , 0 , -1) #вывод от начала(0) до конца(-1) списка

    if not descs:
        return await message.reply("Ваш список пуст")

    text = "\n".join(f"{i+1}. {d}" for i , d in enumerate(descs)) #i+1 начало с 1, а не нуля.
    await message.answer(text)





@dp.message(F.text == "❌Удалить последнее описание", F.from_user.id == ADMIN_ID)
async def del_decsriprion(message: Message):
    
    descs = await r.rpop(PHRASES_KEY) #pop удаляет ласт описание

    if not descs:
        return await message.reply("Ваш список на данный момент пуст")

    await message.answer("⚠️Ваше последние описание удалено")




@dp.message(F.text == "🗑Удалить все описания", F.from_user.id == ADMIN_ID)
async def del_all_decsriprion(message: Message):

    descs = await r.delete(PHRASES_KEY) #удаляет вообще весь список

    if not descs:
        return await message.reply("Ваш список на данный момент итак пуст") 
    await message.answer("⚠️Ваш список полностью удален")



@dp.message(Command("deldesc") , F.from_user.id == ADMIN_ID)
async def enumerate_del_cmd(message: Message , command: CommandObject):

    arg = command.args

    if not arg:
        return await message.reply("❌Вы ввели команду неверно.\n Введите корректно команду , например: /deldesc <номер>")

    if not arg.isdigit():
        return await message.reply("❌Вы ввели команду неверно.\n Введите корректно команду , например: /deldesc <номер>")

    index = int(arg) - 1 #что бы не шло с 0, а еденицы 

    descs = await r.lrange(PHRASES_KEY , 0 , -1) #вывод от начала до конца списка для проверки аргументов

    if not descs:
        return await message.reply("❌Ваш список пуст")

    if index < 0 or index > len(descs):
        return await message.reply("❌У вас нет описания с таким номером") #если ввели меньше 0 и больше числа в списке

    removed = descs[index] #запоменаем удаленный номер

    await r.lset(PHRASES_KEY , index , "__TO_DELETE__") #заменяем описание на метку
    await r.lrem(PHRASES_KEY , 0 , "__TO_DELETE__") #удаляем все элементы с этой меткой

    await message.reply(f"⚠️Удалено описание с номером {index+1}:\n{removed}")




@dp.message(Command("setime"), F.from_user.id == ADMIN_ID)
async def set_time(message: Message , command: CommandObject):
    
    descs = await r.lrange(PHRASES_KEY , 0 , -1) #получаем список от начала до конца
    arg = command.args 

    if not descs:
        return await message.reply("❌Ваш список пуст")

    if not arg:
        return await message.answer("❌Введите правильный формат: /setime 6h(или 30m, 1h, 10s)")

    multipliers = {"s" : 1, "m" : 60 , "h": 3600} #таблица перевода в секунды по ключевому значению

    try:
        value = int(float(arg[:-1] or arg) * {"s" : 1, "m" : 60 , "h": 3600}.get(arg[-1], 1))

        #arg[:-1] or arg - срезаем букву оставляя число или если ввели только число , то принимаем его целым без среза
        # * на еденицу времени(час, минута , секунда)
        #get(arg[-1], 1) берёт самую последнюю букву , а 1 это деф значения без буквы времени(s,m,h)

    except (ValueError, KeyError):
        return await message.reply("❌Неверный формат.Введите правильный формат: /setime 6h(или 30m, 1h, 10s)")

    await r.set(TIMER_KEY, value) #сохраняем(set)
    await message.reply(f"⚠️Время смены описаний: {arg}")



@dp.message()
async def def_user_msg(message: Message):
    await message.reply("❌У вас недостаточно прав.Только пользователи с правами администратора имеют доступ к этой команде")



async def route_descriptions():
    last_desc = None #последнее описание
    while True:
        try:

            interval = int(await r.get(TIMER_KEY) or 6 * 60 * 60) #берем сохраненный интервал(get) или выбирается дефолтный
            descs = await r.lrange(PHRASES_KEY , 0 , -1) #достаем весь список

            if not descs:
                logging.warning("Список пуст.Спим час")#логгируем лог лог лог
                await asyncio.sleep(3600)#если нет описания то в инактив на час
                continue

            valid_desc = [d for d in descs if d != last_desc] #выкидываем фразу если она совпала в цикле
            #данную карусель я провел потому, что во время тестов он менял на фразу которая стояла в канале и бот крч падал
            if not valid_desc:
                valid_desc = descs #если нет списка то переключаемся на основе готового(например 1 фраза осталась)

            desc = random.choice(valid_desc)#меняем на рандом

            try:
                await bot.set_chat_description(chat_id=CHANNEL_ID, description=desc) #меняем описание
                last_desc = desc #запонимаем фразу после каждого круга
                logging.info(f"Описание изменино на {desc}")#проверяем поменялось ли описание

            except Exception as e:
                logging.error(f"Error updating channel description: {e}")
            await asyncio.sleep(interval) #уйдет спать в заданное время

        except Exception as global_e:
            logging.critical(f"Critical error {global_e}")
            await asyncio.sleep(60) #Спим минуту



async def main():
    asyncio.create_task(route_descriptions())
    await dp.start_polling(bot , polling_timeout=15, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())