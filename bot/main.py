import asyncio, os, json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from rag.answer import answer
from recommender.engine import pick_electives
from recommender.rules import Profile

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")

dp = Dispatcher()
bot = Bot(TOKEN, parse_mode="HTML")

KB_MAIN = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/compare")],
              [KeyboardButton(text="/plan")],
              [KeyboardButton(text="/electives")],
              [KeyboardButton(text="/help")]], resize_keyboard=True)

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "Привет! Я помогу сравнить магистратуры ИТМО: «Искусственный интеллект» и «AI Product». "
        "Задавайте вопросы по учебным планам, дисциплинам, ECTS, семестрам и поступлению.",
        reply_markup=KB_MAIN
    )

@dp.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer("Команды: /compare — различия, /plan — план по семестрам, /electives — рекомендации по выборным.")

@dp.message(Command("compare"))
async def compare(m: Message):
    a1 = answer("чем отличается программа", program="AI")["text"]
    a2 = answer("чем отличается программа", program="AI Product")["text"]
    await m.answer("<b>AI</b>\n" + a1 + "\n\n<b>AI Product</b>\n" + a2)

@dp.message(Command("plan"))
async def plan(m: Message):
    txt = answer("план обучения по семестрам", program=None)["text"]
    await m.answer(txt)

@dp.message(Command("electives"))
async def electives(m: Message):
    # simple interactive shortcut: assume some defaults
    profile = Profile(background=["product"], level="junior", interests=["analytics"], workload="medium")
    rec = pick_electives(profile, "AI Product")
    def fmt(lst):
        return "\n".join([f"• {c['name']} (сем {c['semester']}, {c['ects']} ECTS) — {c['source_ref']}" for c in lst])
    txt = "<b>Рекомендации выборных (AI Product)</b>\n"               "<i>primary</i>\n" + fmt(rec["primary"]) + "\n\n" +               "<i>secondary</i>\n" + fmt(rec["secondary"]) + "\n\n" +               "<i>stretch</i>\n" + fmt(rec["stretch"])
    await m.answer(txt)

@dp.message()
async def generic(m: Message):
    q = m.text or ""
    res = answer(q)
    await m.answer(res["text"])

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
