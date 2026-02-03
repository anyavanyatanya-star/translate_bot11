import os
import shutil
import yt_dlp
from faster_whisper import WhisperModel
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ================== НАСТРОЙКИ ==================
TOKEN = os.getenv("8377974321:AAG1VqQNq7vWnrQI_HvffSGe1ljyKZn0di0")
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# CPU модель (лёгкая)
model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

# ================== ОБРАБОТКА ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    if not link.startswith("http"):
        await update.message.reply_text("❌ Это не ссылка")
        return

    user_id = update.effective_user.id
    audio_base = os.path.join(DOWNLOAD_DIR, str(user_id))
    audio_path = audio_base + ".mp3"

    await update.message.reply_text("⏳ Скачиваю аудио...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": audio_base,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
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

    await update.message.reply_text("🎧 Расшифровываю...")

    try:
        segments, _ = model.transcribe(audio_path, language="ru")
        text = "".join(segment.text for segment in segments).strip()
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка распознавания:\n{e}")
        return

    if not text:
        await update.message.reply_text("❌ Текст пустой")
        return

    if len(text) > 4000:
        txt_path = audio_base + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        await update.message.reply_document(open(txt_path, "rb"))
        os.remove(txt_path)
    else:
        await update.message.reply_text(text)

    # 🧹 ЧИСТКА
    if os.path.exists(audio_path):
        os.remove(audio_path)

# ================== ЗАПУСК ==================
if name == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен")
    app.run_polling()
