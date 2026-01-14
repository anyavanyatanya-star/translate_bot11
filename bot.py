import os
import asyncio
import yt_dlp
import whisper
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import logging
import torch

# Токен бота
BOT_TOKEN = "8377974321:AAG1VqQNq7vWnrQI_HvffSGe1ljyKZn0di0"

# Создаем папку для загрузки
os.makedirs("downloads", exist_ok=True)

# Определяем устройство: CUDA если доступна, иначе CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Используем устройство: {DEVICE}")

# Загружаем модель Whisper на нужное устройство
model = whisper.load_model("tiny", device=DEVICE)

# Функция для скачивания аудио с видео по ссылке
def download_audio(url):
    ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": "downloads/audio.%(ext)s",
    "quiet": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
    }],
    "jsruntimes": ["node"],  # <- добавь эту строчку
}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "downloads/audio.mp3"

# Функция для расшифровки аудио в текст
async def transcribe_audio(path):
    # Запускаем транскрипцию в отдельном потоке, чтобы не блокировать Telegram
    result = await asyncio.to_thread(model.transcribe, path)
    return result["text"], result["language"]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Привет!\n\n"
        "Я могу расшифровать аудио с видео. Просто отправь мне ссылку на YouTube или TikTok!"
    )

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Получено сообщение: {update.message.text}")  # Логирование
    text = update.message.text

    if "http" not in text:
        await update.message.reply_text("❌ Похоже, это не ссылка")
        return

    await update.message.reply_text("⏳ Обрабатываю...")

    try:
        audio_path = download_audio(text)
        transcription, lang = await transcribe_audio(audio_path)

        await update.message.reply_text(
            f"📝 Текст ({lang}):\n\n{transcription[:4000]}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# Основная функция запуска бота
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен")
    await app.run_polling()

# Запуск бота
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
