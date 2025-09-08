import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Токен берём из переменных окружения (Railway/Render)
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Не найден TOKEN! Укажи его в переменных окружения Railway/Render.")

bot = Bot(TOKEN)
dp = Dispatcher()

# ===== Суровые вопросы =====
questions = [
    "Что важнее: свобода или стабильность?",
    "Веришь ли ты, что человек полностью отвечает за свою судьбу?",
    "Что для тебя важнее в жизни: деньги или смысл?",
    "Нужно ли всегда говорить правду, даже если она ранит?",
    "Способен ли ты простить предательство близкого?",
    "Семья или карьера — что в приоритете?",
    "Веришь ли ты в любовь на всю жизнь?",
    "Лучше быть лидером или частью команды?",
    "Что важнее: успех или счастье?",
    "Считаешь ли ты, что прошлое определяет будущее?",
    "Готов ли ты пожертвовать комфортом ради мечты?",
    "Нужно ли помогать людям, даже если они не благодарят?",
    "Лучше прожить короткую, но яркую жизнь или длинную и спокойную?",
    "Считаешь ли ты, что человек может измениться кардинально?",
    "Что для тебя важнее: уважение или любовь?",
    "Справедливо ли иногда поступить жестко ради общего блага?",
    "Деньги делают людей счастливыми?",
    "Нужно ли всегда подчиняться закону?",
    "Что важнее: честь или успех?",
    "Готов ли ты рискнуть всем ради идеи?",
    "Что сильнее: разум или эмоции?",
    "Стоит ли всегда доверять только себе?"
]

# Хранилище ответов
user_answers = {}   # {user_id: {"step": int, "answers": []}}
quiz_links = {}     # {friend_id: owner_id}
finished_users = {} # {user_id: answers} — ответы первого человека

# ===== Старт =====
@dp.message(Command("start"))
async def start(message: types.Message):
    user_answers[message.from_user.id] = {"step": 0, "answers": []}
    await message.answer("👋 Привет! Давай проверим вашу совместимость.\n\nОтвечай на 22 вопроса.")
    await message.answer(questions[0])

# ===== Ответы первого пользователя =====
@dp.message()
async def quiz(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_answers:
        return

    data = user_answers[user_id]
    step = data["step"]

    if step < len(questions):
        data["answers"].append(message.text.strip().lower())
        data["step"] += 1

    if data["step"] < len(questions):
        await message.answer(questions[data["step"]])
    else:
        finished_users[user_id] = data["answers"]
        link = f"/quiz {user_id}"
        await message.answer(
            f"✅ Ты прошёл тест! Теперь скинь другу эту ссылку: `{link}`",
            parse_mode="Markdown"
        )
        del user_answers[user_id]

# ===== Друг начинает тест =====
@dp.message(Command("quiz"))
async def start_friend_quiz(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используй: /quiz ID")
        return

    owner_id = int(args[1])
    friend_id = message.from_user.id

    if owner_id not in finished_users:
        await message.answer("❌ Этот тест ещё не создан или устарел.")
        return

    quiz_links[friend_id] = owner_id
    user_answers[friend_id] = {"step": 0, "answers": []}

    await message.answer("🔥 Отлично! Ты проходишь тест для друга. Отвечай честно 😉")
    await message.answer(questions[0])

# ===== Друг отвечает =====
@dp.message()
async def friend_quiz(message: types.Message):
    friend_id = message.from_user.id
    if friend_id not in user_answers:
        return

    data = user_answers[friend_id]
    step = data["step"]

    data["answers"].append(message.text.strip().lower())
    data["step"] += 1

    if data["step"] < len(questions):
        await message.answer(questions[data["step"]])
    else:
        owner_id = quiz_links.get(friend_id)
        if not owner_id:
            return

        owner_answers = finished_users.get(owner_id, [])
        friend_answers = data["answers"]

        matches = sum(1 for a, b in zip(owner_answers, friend_answers) if a == b)
        percent = round(matches / len(questions) * 100)

        await message.answer(f"🎉 Совместимость с другом: {percent}%")
        await bot.send_message(
            owner_id,
            f"🎉 Твой друг @{message.from_user.username or message.from_user.first_name} "
            f"прошёл тест! Совместимость: {percent}%"
        )

        # Чистим
        del user_answers[friend_id]
        del quiz_links[friend_id]


# ===== Запуск =====
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
