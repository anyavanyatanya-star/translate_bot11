import os
import yt_dlp
import whisper
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ================== НАСТРОЙКИ ==================
TOKEN = os.getenv("8377974321:AAG1VqQNq7vWnrQI_HvffSGe1ljyKZn0di0")  # твой Telegram токен
DOWNLOAD_DIR = "downloads"

# Создаем папку для скачивания
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Загружаем модель Whisper (работаем на CPU)
model = whisper.load_model("small")
print("🤖 Whisper модель загружена, бот готов к работе!")

# ================== ОБРАБОТКА СООБЩЕНИЙ ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    if not link.startswith("http"):
        await update.message.reply_text("❌ Похоже, это не ссылка")
        return

    await update.message.reply_text("⏳ Скачиваю аудио...")

    audio_base = os.path.join(DOWNLOAD_DIR, str(update.effective_user.id))
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
        }],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка загрузки:\n{e}")
        return

    if not os.path.exists(audio_path):
        await update.message.reply_text("❌ Аудио не найдено")
        return

    await update.message.reply_text("🎧 Расшифровываю аудио...")

    try:
        result = model.transcribe(audio_path, language="ru", task="transcribe")
        text = result["text"].strip()
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка Whisper:\n{e}")
        return

    # Отправка результата пользователю
    if len(text) > 4000:
        txt_path = os.path.join(DOWNLOAD_DIR, f"text_{update.effective_user.id}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        await update.message.reply_document(open(txt_path, "rb"))
        os.remove(txt_path)
    else:
        await update.message.reply_text(text)

    # Удаляем аудио после обработки
    os.remove(audio_path)

# ================== ЗАПУСК БОТА ==================
if name == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен! Ожидаю ссылки на видео или аудио...")
    app.run_polling()
    
