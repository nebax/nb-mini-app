import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, MenuButtonDefault, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)
    
BOT_TOKEN = "9245323400:AAE-4eHLSm_0eBtodG7qp6Sz6DtTDWMGeg0"
ADMIN_GROUP_ID = -100387124942
MINI_APP_URL = "https://nb-mini-app.vercel.app"

# Storage
approved_users = {}      # {user_id: "Grade 10"}
pending_selections = {}  # {user_id: "Grade 10"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in approved_users:
        await context.bot.set_chat_menu_button(
            chat_id=user_id,
            menu_button=MenuButtonDefault()
        )

    if user_id in approved_users:
        user_grade = approved_users[user_id]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Open NB Exam Portal", web_app=WebAppInfo(url=f"{MINI_APP_URL}?grade={user_grade}"))]
        ])
        text = f"🎓 **Welcome back to NB Tutorial Service!**\n\nYour active plan: **{user_grade}**\nTap below to start practicing:"
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Grade 8", callback_data="select_Grade 8"), InlineKeyboardButton("Grade 9", callback_data="select_Grade 9")],
            [InlineKeyboardButton("Grade 10", callback_data="select_Grade 10"), InlineKeyboardButton("Grade 11", callback_data="select_Grade 11")],
            [InlineKeyboardButton("🎓 Grade 12 (Entrance Exam)", callback_data="select_Grade 12 Entrance")]
        ])
        text = (
            "👋 **Welcome to NB Tutorial Service Exam Portal!**\n\n"
            "Please select your grade below to get started:"
        )
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def grade_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_grade = query.data.split("select_")[1]
    user_id = query.from_user.id
    pending_selections[user_id] = selected_grade

    if selected_grade == "Grade 12 Entrance":
        price = "250 ETB"
        access_info = "Full access to Grades 9, 10, 11, and 12 Entrance Exam questions"
    else:
        price = "200 ETB"
        access_info = f"Access to {selected_grade} Exam questions"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Payment Info (CBE / Telebirr)", callback_data="pay_info")]
    ])

    text = (
        f"✅ You selected: **{selected_grade}**\n\n"
        f"📌 **Access included:** {access_info}\n"
        f"💵 **Subscription Fee:** {price}\n\n"
        f"Click below to get payment instructions:"
    )
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "💳 **NB Tutorial Service - Payment Instructions**\n\n"
        "• **CBE Account:** `1000724373686` (Nebyu Endashaw)\n"
        "• **Telebirr Number:** `0974539791` (Nebyu Endashaw)\n\n"
        "📸 **Next Step:** Take a clear screenshot of your payment receipt and send it directly into this chat."
    )
    await query.edit_message_text(text, parse_mode="Markdown")

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    selected_grade = pending_selections.get(user_id, "Not Specified")

    caption = (
        f"📥 **New Payment Submission**\n\n"
        f"👤 **Name:** {user.full_name}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"📚 **Selected Grade:** {selected_grade}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ])

    if update.message.photo:
        await context.bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    elif update.message.document:
        await context.bot.send_document(
            chat_id=ADMIN_GROUP_ID,
            document=update.message.document.file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    await update.message.reply_text("Your payment screenshot has been submitted! We will verify it shortly.")

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id_str = query.data.split("_")
    user_id = int(user_id_str)

    if action == "approve":
        grade = pending_selections.get(user_id, "Grade 8")
        approved_users[user_id] = grade

        await context.bot.set_chat_menu_button(
            chat_id=user_id,
            menu_button=MenuButtonWebApp(
                text="NB Exam prep",
                web_app=WebAppInfo(url=f"{MINI_APP_URL}?grade={grade}")
            )
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Open NB Exam Portal", web_app=WebAppInfo(url=f"{MINI_APP_URL}?grade={grade}"))]
        ])

        if grade == "Grade 12 Entrance":
            msg = "Payment Approved! You now have full access to Grade 9, 10, 11 & 12 Entrance Exams."
        else:
            msg = f"Payment Approved! You now have access to {grade} Exam questions."

        await context.bot.send_message(chat_id=user_id, text=f"🎉 {msg}\n\nClick below to start practicing:", reply_markup=keyboard)
        await query.edit_message_caption(caption=query.message.caption + f"\n\n✅ APPROVED ({grade})")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Payment receipt rejected. Please make sure the transaction details are clear and re-submit."
        )
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ REJECTED")

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Clear old webhooks automatically on startup
    import asyncio
    asyncio.run(app.bot.delete_webhook(drop_pending_updates=True))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(grade_selection, pattern="^select_"))
    app.add_handler(CallbackQueryHandler(payment_info, pattern="^pay_info$"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_screenshot))

    print("Bot is running...")
    app.run_polling()
