import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler, ConversationHandler
)

# ─── SOZLAMALAR ────────────────────────────────────────────────
TOKEN    = "SIZNING_BOT_TOKENINGIZ"   # @BotFather dan oling
ADMIN_ID = 123456789                  # @userinfobot dan oling

PODCASTS_FILE = "podcasts.json"

logging.basicConfig(level=logging.INFO)

# ─── HOLAT KONSTANTALARI (ConversationHandler uchun) ───────────
(
    WAIT_CODE, WAIT_TITLE, WAIT_SHORT_DESC, WAIT_FULL_DESC,
    WAIT_QUOTES, WAIT_SUMMARY, WAIT_AUDIO, WAIT_VIDEO
) = range(8)

# ─── JSON YORDAMCHILAR ─────────────────────────────────────────
def load():
    if os.path.exists(PODCASTS_FILE):
        with open(PODCASTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save(data):
    with open(PODCASTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── FOYDALANUVCHI TOMONLARI ───────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙 *Podcast Kutubxonasiga Xush Kelibsiz!*\n\n"
        "Podcastni topish uchun uning *kodini* yuboring.\n"
        "📌 Misol: `P001`\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Admin: /admin",
        parse_mode="Markdown"
    )

async def search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    data = load()

    if code not in data:
        await update.message.reply_text(
            f"❌ *{code}* kodi topilmadi.\n"
            "Kodni tekshirib qayta yuboring.",
            parse_mode="Markdown"
        )
        return

    p = data[code]
    keyboard = [
        [
            InlineKeyboardButton("📝 Tavsif",      callback_data=f"desc|{code}"),
            InlineKeyboardButton("💬 Iqtiboslar",  callback_data=f"quotes|{code}"),
        ],
        [
            InlineKeyboardButton("📋 Qisqa Hulosa", callback_data=f"summary|{code}"),
        ],
        [
            InlineKeyboardButton("🎵 Audio",        callback_data=f"audio|{code}"),
            InlineKeyboardButton("🎬 Video",         callback_data=f"video|{code}"),
        ],
    ]
    text = (
        f"🎙 *{p['title']}*\n"
        f"🔖 Kod: `{code}`\n\n"
        f"_{p['short_desc']}_\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Quyidagi bo'limlardan birini tanlang 👇"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action, code = q.data.split("|", 1)
    data = load()
    p = data.get(code)
    if not p:
        await q.message.reply_text("❌ Podcast topilmadi.")
        return

    back = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Ortga", callback_data=f"back|{code}")
    ]])

    if action == "desc":
        await q.message.reply_text(
            f"📝 *To'liq Tavsif — {p['title']}*\n\n{p['full_desc']}",
            parse_mode="Markdown", reply_markup=back
        )
    elif action == "quotes":
        await q.message.reply_text(
            f"💬 *Iqtiboslar — {p['title']}*\n\n{p['quotes']}",
            parse_mode="Markdown", reply_markup=back
        )
    elif action == "summary":
        await q.message.reply_text(
            f"📋 *Qisqa Hulosa — {p['title']}*\n\n{p['summary']}",
            parse_mode="Markdown", reply_markup=back
        )
    elif action == "audio":
        fid = p.get("audio_file_id")
        if fid:
            await q.message.reply_audio(audio=fid, caption=f"🎵 {p['title']}")
        else:
            await q.message.reply_text("⏳ Audio hali yuklanmagan.")
    elif action == "video":
        fid = p.get("video_file_id")
        if fid:
            await q.message.reply_video(video=fid, caption=f"🎬 {p['title']}")
        else:
            await q.message.reply_text("⏳ Video hali yuklanmagan.")
    elif action == "back":
        await search_by_code(q.message, code, data)

async def search_by_code(message, code, data):
    p = data[code]
    keyboard = [
        [
            InlineKeyboardButton("📝 Tavsif",      callback_data=f"desc|{code}"),
            InlineKeyboardButton("💬 Iqtiboslar",  callback_data=f"quotes|{code}"),
        ],
        [
            InlineKeyboardButton("📋 Qisqa Hulosa", callback_data=f"summary|{code}"),
        ],
        [
            InlineKeyboardButton("🎵 Audio",        callback_data=f"audio|{code}"),
            InlineKeyboardButton("🎬 Video",         callback_data=f"video|{code}"),
        ],
    ]
    text = (
        f"🎙 *{p['title']}*\n"
        f"🔖 Kod: `{code}`\n\n"
        f"_{p['short_desc']}_\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Quyidagi bo'limlardan birini tanlang 👇"
    )
    await message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── ADMIN: PODCAST QO'SHISH (step-by-step) ───────────────────

async def admin_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Ruxsat yo'q.")
        return ConversationHandler.END
    await update.message.reply_text(
        "🔐 *Admin Paneli*\n\n"
        "Yangi podcast kodi yuboring:\n"
        "📌 Misol: `P001`",
        parse_mode="Markdown"
    )
    return WAIT_CODE

async def get_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["code"] = update.message.text.strip().upper()
    await update.message.reply_text("✅ Kod saqlandi.\n\nPodcast *sarlavhasini* yuboring:", parse_mode="Markdown")
    return WAIT_TITLE

async def get_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["title"] = update.message.text.strip()
    await update.message.reply_text("✅ Sarlavha saqlandi.\n\n*Qisqa tavsif* yuboring (1-2 jumla):", parse_mode="Markdown")
    return WAIT_SHORT_DESC

async def get_short_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["short_desc"] = update.message.text.strip()
    await update.message.reply_text("✅ Qisqa tavsif saqlandi.\n\n*To'liq tavsif* yuboring:", parse_mode="Markdown")
    return WAIT_FULL_DESC

async def get_full_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["full_desc"] = update.message.text.strip()
    await update.message.reply_text("✅ To'liq tavsif saqlandi.\n\n*Iqtiboslar* yuboring (har biri yangi qatorda):", parse_mode="Markdown")
    return WAIT_QUOTES

async def get_quotes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["quotes"] = update.message.text.strip()
    await update.message.reply_text("✅ Iqtiboslar saqlandi.\n\n*Qisqa hulosa* yuboring:", parse_mode="Markdown")
    return WAIT_SUMMARY

async def get_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["summary"] = update.message.text.strip()
    await update.message.reply_text("✅ Hulosa saqlandi.\n\n🎵 *Audio faylni* yuboring:", parse_mode="Markdown")
    return WAIT_AUDIO

async def get_audio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.audio:
        await update.message.reply_text("❌ Iltimos audio fayl yuboring (.mp3 va h.k.)")
        return WAIT_AUDIO
    ctx.user_data["audio_file_id"] = update.message.audio.file_id
    await update.message.reply_text("✅ Audio saqlandi.\n\n🎬 *Video faylni* yuboring:", parse_mode="Markdown")
    return WAIT_VIDEO

async def get_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("❌ Iltimos video fayl yuboring.")
        return WAIT_VIDEO

    ctx.user_data["video_file_id"] = update.message.video.file_id
    d = ctx.user_data
    code = d["code"]

    podcasts = load()
    podcasts[code] = {
        "title":         d["title"],
        "short_desc":    d["short_desc"],
        "full_desc":     d["full_desc"],
        "quotes":        d["quotes"],
        "summary":       d["summary"],
        "audio_file_id": d["audio_file_id"],
        "video_file_id": d["video_file_id"],
    }
    save(podcasts)

    await update.message.reply_text(
        f"🎉 *Podcast muvaffaqiyatli qo'shildi!*\n\n"
        f"🔖 Kod: `{code}`\n"
        f"🎙 Sarlavha: {d['title']}\n\n"
        "Foydalanuvchilar endi bu kodni kiritib podcast olishi mumkin!",
        parse_mode="Markdown"
    )
    ctx.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

# ─── MAIN ──────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Admin suhbati
    conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_start)],
        states={
            WAIT_CODE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
            WAIT_TITLE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            WAIT_SHORT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_short_desc)],
            WAIT_FULL_DESC:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_desc)],
            WAIT_QUOTES:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quotes)],
            WAIT_SUMMARY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summary)],
            WAIT_AUDIO:      [MessageHandler(filters.AUDIO, get_audio)],
            WAIT_VIDEO:      [MessageHandler(filters.VIDEO, get_video)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    print("🚀 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
