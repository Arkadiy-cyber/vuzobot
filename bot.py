import sqlite3
import logging
import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, PreCheckoutQuery
from aiogram import F

TOKEN = "8677752852:AAEIIwPvj_oFStIRvPGoh1Ue7aU6CCFS4DM"
PROVIDER_TOKEN = "390540012:LIVE:97243"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

conn = sqlite3.connect('universities.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS universities (
        name TEXT,
        program TEXT,
        score INTEGER,
        url TEXT,
        city TEXT
    )
''')
conn.commit()

class Form(StatesGroup):
    profile_choice = State()
    rus = State()
    math = State()
    profile_subject = State()

profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔧 Технический")],
        [KeyboardButton(text="📚 Гуманитарный")],
        [KeyboardButton(text="🔬 Естественно-научный")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("🎓 Привет! Выбери свой профиль:", reply_markup=profile_kb)
    await state.set_state(Form.profile_choice)

@dp.message(Form.profile_choice)
async def profile_chosen(message: types.Message, state: FSMContext):
    text = message.text
    if text == "🔧 Технический":
        await state.update_data(profile="tech")
    elif text == "📚 Гуманитарный":
        await state.update_data(profile="human")
    elif text == "🔬 Естественно-научный":
        await state.update_data(profile="science")
    else:
        await message.answer("Нажми на кнопку!")
        return
    await message.answer("Введи балл по РУССКОМУ языку (0-100):")
    await state.set_state(Form.rus)

@dp.message(Form.rus)
async def get_rus(message: types.Message, state: FSMContext):
    await state.update_data(rus=message.text)
    await message.answer("Введи балл по МАТЕМАТИКЕ:")
    await state.set_state(Form.math)

@dp.message(Form.math)
async def get_math(message: types.Message, state: FSMContext):
    await state.update_data(math=message.text)
    data = await state.get_data()
    if data["profile"] == "tech":
        await message.answer("Введи балл по ФИЗИКЕ или ИНФОРМАТИКЕ:")
    elif data["profile"] == "human":
        await message.answer("Введи балл по ОБЩЕСТВОЗНАНИЮ, ИСТОРИИ или ИНОСТРАННОМУ ЯЗЫКУ:")
    else:
        await message.answer("Введи балл по БИОЛОГИИ или ХИМИИ:")
    await state.set_state(Form.profile_subject)

@dp.message(Form.profile_subject)
async def get_profile_subject(message: types.Message, state: FSMContext):
    data = await state.update_data(prof_subj=message.text)
    await state.clear()
    try:
        total = int(data['rus']) + int(data['math']) + int(message.text)
    except ValueError:
        await message.answer("Ошибка: вводи только числа. Начни с /start")
        return
    cursor.execute("SELECT name, program, score, url, city FROM universities WHERE score <= ? ORDER BY score DESC", (total,))
    results = cursor.fetchall()
    if not results:
        await message.answer("😞 Нет вузов по твоим баллам. Попробуй другие цифры.")
        return

    answer = "🎉 Вот подходящие вузы (бесплатно):\n\n"
    for i, (name, program, score, url, city) in enumerate(results[:5], 1):
        answer += f"{i}. *{name}* ({city})\n   {program}\n   Проходной: {score}\n   {url}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 100 ₽ и получить ТОП-20", pay=True)],
    ])
    await message.answer_invoice(
        title="Полный список вузов (ТОП-20)",
        description="Все подходящие направления с проходными баллами и ссылками на сайты.",
        payload=f"total_{total}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Доступ к ТОП-20", amount=10000)],
        reply_markup=keyboard,
    )
    await message.answer(answer, parse_mode="Markdown")

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_pay(message: types.Message):
    total_score = int(message.successful_payment.invoice_payload.split('_')[1])
    cursor.execute("SELECT name, program, score, url, city FROM universities WHERE score <= ? ORDER BY score DESC", (total_score,))
    results = cursor.fetchall()
    if not results:
        await message.answer("❌ По твоим баллам не найдено вузов.")
        return
    answer = "🎉 *Полный список вузов (ТОП-20) по твоим баллам:*\n\n"
    for i, (name, program, score, url, city) in enumerate(results[:20], 1):
        answer += f"{i}. *{name}* ({city})\n   {program}\n   ✅ Проходной: {score}\n   🔗 {url}\n\n"
    await message.answer(answer, parse_mode="Markdown")

# ----- Flask-приложение для вебхука -----
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    update_data = request.get_json()
    update = types.Update(**update_data)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.feed_update(bot, update))
    return 'OK', 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    return "Webhook was set manually via console.", 200


