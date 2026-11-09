import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ⚠️ REPLACE THESE 3 VALUES WITH YOUR ACTUAL DATA
BOT_TOKEN = "9245323400:AAE-4eHLSm_0eBtodG7qP6Sz6DtTDWMGeg0"
ADMIN_GROUP_ID = -1003871242942  # Your group ID from Step 1
MINI_APP_URL = "https://your-app.vercel.app"  # Your Vercel URL from Step 2

approved_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in approved_users:
        keyboard = [
            [InlineKeyboardButton("🚀 Open NB Exam Portal", web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
        text = "🎓 **Welcome back to NB Tutorial Service!**\n\nTap below to start practicing questions:"
    else:
        keyboard = [
            [InlineKeyboardButton("💳 Payment Info (CBE / Telebirr)", callback_data="pay_info")],
        ]
        text = (
            "👋 **Welcome to NB Tutorial Service Exam Portal!**\n\n"
            "Unlock access to Grade 9–12 and Entrance Exam questions with detailed explanations.\n\n"
            "**How to get access:**\n"
            "1. Pay the subscription fee via Telebirr or CBE.\n"
            "2. Send a screenshot of your payment receipt directly to this chat."
        )
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "💳 **NB Tutorial Service - Payment Instructions**\n\n"
        "• **CBE Account:** `1000724373686` (Nebyu Endashaw)\n"
        "• **Telebirr Number:** `0974539791` (Nebyu Endashaw)\n\n"
        "📸 **Next Step:** Take a clear screenshot of your payment receipt and send it directly into this chat."
    )
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_start")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]

    # Forward photo to your Admin Group (replace YOUR_ADMIN_GROUP_ID with your actual group ID)
    await context.bot.send_photo(
        chat_id=YOUR_ADMIN_GROUP_ID,
        photo=photo_file_id,
        caption=f"New Payment Receipt\nUser: {user.full_name}\nUsername: @{user.username}\nID: {user.id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Plain text reply to the user (NO parse_mode)
    await update.message.reply_text("Your payment screenshot has been submitted! We will verify it shortly.")
    ]
    
    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=photo_file_id,
        caption=f"📩 **New Payment Submission**\n\nUser: {user.full_name}\nUsername: @{user.username}\nID: `{user.id}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    await update.message.reply_text("⏳ Screenshot received! Our admins are reviewing your receipt. Access will be activated shortly.")

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id_str = query.data.split("_")
    user_id = int(user_id_str)

    if action == "approve":
        approved_users.add(user_id)
        keyboard = [[InlineKeyboardButton("🚀 Open NB Exam Portal", web_app=WebAppInfo(url=MINI_APP_URL))]]
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 **Payment Approved!** You now have full access to NB Tutorial Service Exam Portal. Click below to practice:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ **APPROVED**", parse_mode="Markdown")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Payment receipt rejected. Please make sure the transaction details are clear and re-submit.",
        )
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ **REJECTED**", parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(payment_info, pattern="^pay_info$"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_start$"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))

    print("NB Tutorial Bot is running...")
    app.run_polling()
