import os
import logging
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest

# --- خواندن کلیدها از تنظیمات امن سرور ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

# لینک شبکه‌های اجتماعی (این بخش را با لینک خودتان عوض کنید)
YOUTUBE_LINK = "https://www.youtube.com/@AR_ytt
INSTAGRAM_LINK = "https://www.instagram.com/ar_yttt?utm_source=qr&rpxt=MWNsZGkwcGxrMHJtbA==
TIKTOK_LINK = "https://tiktok.com/@parvaz.yt1

client = OpenAI(
    base_url="https://groq.com",
    api_key=GROQ_API_KEY
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
waiting_for_feedback = set()

async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not CHANNEL_ID:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest:
        return False

def join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال تلگرام (اجباری)", url=f"https://t.me{CHANNEL_ID.replace('@', '')}")],
        [
            InlineKeyboardButton("▶️ یوتیوب", url=YOUTUBE_LINK),
            InlineKeyboardButton("📸 اینستاگرام", url=INSTAGRAM_LINK),
            InlineKeyboardButton("🎵 تیک‌تاک", url=TIKTOK_LINK)
        ],
        [InlineKeyboardButton("🔄 بررسی عضویت و ورود به ربات", callback_data='check_join')]
    ]
    return InlineKeyboardMarkup(keyboard)

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📩 ارسال پیشنهاد یا انتقاد به مدیر", callback_data='send_feedback')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    waiting_for_feedback.discard(user_id)

    if not await is_user_member(user_id, context):
        text = (
            "⛔️ برای استفاده رایگان از ربات هوش مصنوعی، ابتدا در کانال تلگرام ما عضو شوید و شبکه‌های اجتماعی ما را دنبال کنید:\n\n"
            "پس از عضویت در کانال، روی دکمه **بررسی عضویت** بزنید 👇"
        )
        await update.message.reply_text(text, reply_markup=join_keyboard(), parse_mode="Markdown")
        return

    await update.message.reply_text(
        "سلام! 👋\nبه ربات هوش مصنوعی خوش آمدید.\nهر سوالی دارید بپرسید تا فوری جواب بدهم! 🤖✨",
        reply_markup=main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'check_join':
        if await is_user_member(user_id, context):
            await query.edit_message_text(
                "✅ عضویت شما تایید شد!\nحالا هر سوالی دارید بپرسید تا هوش مصنوعی پاسخ دهد:",
                reply_markup=main_keyboard()
            )
        else:
            await query.answer("❌ شما هنوز در کانال تلگرام عضو نشده‌اید!", show_alert=True)

    elif query.data == 'send_feedback':
        waiting_for_feedback.add(user_id)
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data='cancel_feedback')]]
        await query.message.reply_text(
            "✍️ لطفاً پیشنهاد، انتقاد یا پیام خود را برای مدیر بنویسید و ارسال کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == 'cancel_feedback':
        waiting_for_feedback.discard(user_id)
        await query.edit_message_text("✅ ارسال پیشنهاد لغو شد. می‌توانید دوباره با هوش مصنوعی صحبت کنید.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id in waiting_for_feedback:
        waiting_for_feedback.discard(user_id)
        feedback_text = update.message.text
        admin_message = (
            f"📩 **پیشنهاد جدید از طرف کاربر:**\n\n"
            f"👤 نام: {user.full_name}\n"
            f"🆔 آیدی عددی: `{user_id}`\n"
            f"🔗 یوزرنیم: @{user.username if user.username else 'ندارد'}\n\n"
            f"📝 **متن پیام:**\n{feedback_text}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode="Markdown")
            await update.message.reply_text("✅ ممنون! پیشنهاد شما با موفقیت برای مدیر ارسال شد.")
        except Exception:
            await update.message.reply_text("⚠️ خطایی در ارسال پیام رخ داد. لطفاً بعداً تلاش کنید.")
        return

    if not await is_user_member(user_id, context):
        await start(update, context)
        return

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "تو یک دستیار هوشمند و مفید در تلگرام هستی که به زبان فارسی روان پاسخ می‌دهی."},
                {"role": "user", "content": user_text}
            ]
        )
        reply_text = response.choices[0].message.content
        await update.message.reply_text(reply_text)
    except Exception:
        await update.message.reply_text("⚠️ مشکلی در ارتباط با هوش مصنوعی پیش آمد. لطفاً دوباره تلاش کنید.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == '__main__':
    main()
