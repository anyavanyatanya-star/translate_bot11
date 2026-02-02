import os
import asyncio
import uuid
import whisper
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ================== НАСТРОЙКИ ==================
TOKEN = "8472668826:AAG7miPca8eYkZKWIjng-ChQwnZ94o3n03E"  # твой токен
DOWNLOAD_DIR = "downloads"

# Создаем папку downloads
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Загружаем модель Whisper (CPU)
model = whisper.load_model("tiny")  # можно tiny, small, medium, large

# ================== ФУНКЦИЯ ОБРАБОТКИ СООБЩЕНИЙ ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    if not link.startswith("http"):
        await update.message.reply_text("❌ Это не ссылка")
        return

    await update.message.reply_text("⏳ Скачиваю аудио...")

    # Имя файла уникальное для каждого пользователя
    audio_base = os.path.join(DOWNLOAD_DIR, str(update.effective_user.id) + "_" + str(uuid.uuid4()))
    audio_path = audio_base + ".mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": audio_base,
        "noplaylist": True,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    }

    # Скачивание
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка загрузки:\n{e}")
        return

    if not os.path.exists(audio_path):
        await update.message.reply_text("❌ Аудио не найдено после скачивания")
        return

    await update.message.reply_text("🎧 Расшифровываю...")

    # ===== Транскрипция =====
    try:
        result = model.transcribe(audio_path, language="ru", task="transcribe", fp16=False)
        text = result["text"].strip()
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка транскрипции:\n{e}")
        os.remove(audio_path)
        return

    # ===== Отправка результата =====
    if len(text) > 4000:  # если текст длинный — файл
        txt_path = os.path.join(DOWNLOAD_DIR, f"text_{update.effective_user.id}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        await update.message.reply_document(open(txt_path, "rb"))
        os.remove(txt_path)
    else:
        await update.message.reply_text(text)

    # ===== Чистка мусора =====
    os.remove(audio_path)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен")
    app.run_polling()
    
