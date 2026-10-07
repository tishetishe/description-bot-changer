from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def keyboardpanel() -> ReplyKeyboardMarkup:
	kb = ReplyKeyboardMarkup(resize_keyboard=True)

	btn1 = KeyboardButton("🗒Вывод всех описаний")
	btn2 = KeyboardButton("❌Удалить последнее описание")
	btn3 = KeyboardButton("🗑Удалить все описания")

	kb.add(btn1).add(btn2).add(btn3)
		
	return kb