from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def keyboardpanel() -> ReplyKeyboardMarkup:
	builder = ReplyKeyboardMarkup()

	btn1 = KeyboardButton("🗒Вывод всех описаний")
	btn2 = KeyboardButton("❌Удалить последнее описание")
	btn3 = KeyboardButton("🗑Удалить все описания")

	builder.add(btn1 , btn2 , btn3)

	builder.adjust(1) #рапсположить кнопки в ряд
		
	return builder.as_markup(resize_keyboard=True)