import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import settings.config

API_TOKEN = settings.config.TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


with open('data.json', 'r') as f:
    raw_data = json.load(f)
    for item in raw_data:
        item['month'] = datetime.strptime(item['month'], "%Y-%m-%dT%H:%M:%S.%fZ")

# Создание класса состояний
class Form(StatesGroup):
    month1 = State()
    year1 = State()
    month2 = State()
    year2 = State()
    amount = State()
    year_for_rate = State()


month_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
for month in months:
    month_keyboard.add(KeyboardButton(month))


year_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
years = list(range(1991, 2025))
for year in years:
    year_keyboard.add(KeyboardButton(str(year)))


start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
start_keyboard.add(KeyboardButton("Рассчитать разницу"))
start_keyboard.add(KeyboardButton("Процент за год"))
start_keyboard.add(KeyboardButton("О боте"))
start_keyboard.add(KeyboardButton("Q&A"))


amount_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
amounts = ['1000', '5000', '10000', '100000']
for amount in amounts:
    amount_keyboard.add(KeyboardButton(amount))


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.reply("Добро пожаловать! Выберите одну из опций ниже.", reply_markup=start_keyboard)


@dp.message_handler(Text(equals="О боте", ignore_case=True))
async def cmd_about(message: types.Message):
    await message.reply(
        "Этот бот помогает вычислить сумму на основе процентных изменений за выбранный пользователем период."
        "Выберите 'Рассчитать разницу' или 'Процент за год', чтобы начать расчет."
    )


@dp.message_handler(Text(equals="Q&A", ignore_case=True))
async def cmd_qa(message: types.Message):
    await message.reply(
        "1) Откуда информация?\n"
        "> Большая часть об инфляциях с 1991 года по 2024 была взята с официального сайта РосСтата https://rosstat.gov.ru/\n\n"
        "2) Как происходит расчет?\n"
        "> Существует процент инфляции на конец каждого месяца. За выбранный пользователем период идет перемножение процента концов каждого месяца. "
        "Допустим, вы выбираете 'Январь 1991' и 'Февраль 1991'. Пусть в январе процент 10, в феврале 15, тогда бот перемножает процент, "
        "а дальше полученный коэффициент (1.10 * 1.15) на введенную вами сумму."
        "\n\nВажно, бот выводит сумму, равной на конец выбранного месяца!"
    )


@dp.message_handler(Text(equals="Рассчитать разницу", ignore_case=True))
async def cmd_calculation(message: types.Message):
    await Form.month1.set()
    await message.reply("Выберите первый месяц:", reply_markup=month_keyboard)


@dp.message_handler(state=Form.month1)
async def process_month1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['month1'] = message.text.lower()
    await Form.next()
    await message.reply("Выберите первый год:", reply_markup=year_keyboard)


@dp.message_handler(state=Form.year1)
async def process_year1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['year1'] = int(message.text)
    await Form.next()
    await message.reply("Выберите второй месяц:", reply_markup=month_keyboard)


@dp.message_handler(state=Form.month2)
async def process_month2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['month2'] = message.text.lower()
    await Form.next()
    await message.reply("Выберите второй год:", reply_markup=year_keyboard)


@dp.message_handler(state=Form.year2)
async def process_year2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['year2'] = int(message.text)
    await Form.next()
    await message.reply("Выберите сумму из предложенной (или введите свою):", reply_markup=amount_keyboard)


@dp.message_handler(state=Form.amount)
async def process_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = float(message.text)
        
        month1 = data['month1']
        year1 = data['year1']
        month2 = data['month2']
        year2 = data['year2']
        amount = data['amount']
        
        month_names = {
            'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6,
            'июль': 7, 'август': 8, 'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
        }
        month1_num = month_names[month1]
        month2_num = month_names[month2]
        
        
        start_date = datetime(year1, month1_num, 1)
        end_date = datetime(year2, month2_num, 1)
        filtered_data = [item for item in raw_data if start_date <= item['month'] <= end_date]
        
        
        total_rate = 1
        for item in filtered_data:
            total_rate *= abs(1 + abs(item['rate'] / 100))
        
        final_amount = amount * total_rate

        await message.reply(f"Период: {month1} {year1}г. - {month2} {year2}г.\nИтоговая сумма: {final_amount:.2f} руб.\nПроцент инфляции за данный период:{total_rate:.3f}", reply_markup=start_keyboard)
    
    
    await state.finish()

@dp.message_handler(Text(equals="Процент за год", ignore_case=True))
async def cmd_yearly_rate(message: types.Message):
    await Form.year_for_rate.set()
    await message.reply("Выберите год для расчета процента за год:", reply_markup=year_keyboard)


@dp.message_handler(state=Form.year_for_rate)
async def process_year_for_rate(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        year = int(message.text)
        
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 1)
        filtered_data = [item for item in raw_data if start_date <= item['month'] <= end_date]
        
        
        total_rate = 1
        for item in filtered_data:
            total_rate *= abs(1 + abs(item['rate'] / 100))
        
        await message.reply(f"Перемноженный процент за {year} год: {total_rate:.2f}", reply_markup=start_keyboard)
    
   
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
