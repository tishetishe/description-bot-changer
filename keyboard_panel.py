from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def keyboardpanel() -> ReplyKeyboardMarkup:
	builder = ReplyKeyboardBuilder()

	btn1 = KeyboardButton(text="🗒Вывод всех описаний")
	btn2 = KeyboardButton(text="❌Удалить последнее описание")
	btn3 = KeyboardButton(text="🗑Удалить все описания")

	builder.add(btn1 , btn2 , btn3)

	builder.adjust(1) #рапсположить кнопки в ряд
		
	return builder.as_markup(resize_keyboard=True)