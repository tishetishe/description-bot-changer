from aiogram.types import ReplyKeyboardMarkup , KeyboardButton , InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData



def keyboardpanel() -> ReplyKeyboardMarkup:
	kb = ReplyKeyboardMarkup(keyboard=[
		[KeyboardButton("🗒Вывод всех описаний")],
		[KeyboardButton("❌Удалить последнее описание")],
		[KeyboardButton("🗑Удалить все описания")]
	],resize_keyboard=True) #что бы клавиатура рованой была
	return kb