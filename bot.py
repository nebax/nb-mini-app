import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Configuration & Credentials ---
BOT_TOKEN = "9245323400:AAG3tuluyobP_Y04ACkdzEQnH5V4jGQPn54"
ADMIN_GROUP_ID = -1003871242942
MINI_APP_URL = "https://nb-mini-app.vercel.app"

# --- Storage (In-Memory Tracking) ---
approved_users = {}      # {user_id: "Selected Package Name"}
pending_selections = {}  # {user_id: "Selected Package Name"}

# --- Flask Server for Render Port & Uptime ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "NB Tutorial Bot is alive and running!"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# --- Telegram Bot Command & Callback Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Grade 8 Ministry", callback_data="select_grade_8")],
        [InlineKeyboardButton("📗 Grade 9 Student", callback_data="select_grade_9")],
        [InlineKeyboardButton("📙 Grade 10 Student", callback_data="select_grade_10")],
        [InlineKeyboardButton("🧪 Grade 11 Natural Science", callback_data="select_grade_11_nat")],
        [InlineKeyboardButton("📜 Grade 11 Social Science", callback_data="select_grade_11_soc")],
        [InlineKeyboardButton("🔬 Grade 12 Natural Entrance", callback_data="select_grade_12_nat_entrance")],
        [InlineKeyboardButton("📚 Grade 12 Social Entrance", callback_data="select_grade_12_soc_entrance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to **NB Tutorial Service**!\n\n"
        "Please select your grade and stream below👇🏽:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def grade_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    selected_grade = query.data.split("select_")[1]
    user_id = query.from_user.id
    pending_selections[user_id] = selected_grade

    # Sequential logic checking each grade tier cleanly
    if selected_grade in ["grade_12_nat_entrance", "grade_12_soc_entrance"]:
        price = "200 ETB"
        access_info = f"Full access to {selected_grade.replace('_', ' ').title()} Exam questions"
    elif selected_grade in ["grade_11_nat", "grade_11_soc"]:
        price = "150 ETB"
        access_info = f"Access to {selected_grade.replace('_', ' ').title()} Exam questions"
    elif selected_grade == "grade_10":
        price = "150 ETB"
        access_info = "Access to Grade 10 General Package"
    elif selected_grade == "grade_9":
        price = "150 ETB"
        access_info = "Access to Grade 9 General Package"
    elif selected_grade == "grade_8":
        price = "150 ETB"
        access_info = "Grade 8 Ministry Exam Prep Questions"
    else:
        price = "Standard"
        access_info = f"Access to {selected_grade.replace('_', ' ').title()} Package"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Payment Info (CBE / Telebirr)", callback_data="pay_info")]
    ])
    
    text = (
        f"📌 **Selected Package:** {selected_grade.replace('_', ' ').title()}\n"
        f"💰 **Price:** {price}\n"
        f"📚 **Includes:** {access_info}\n\n"
        "💳 **Payment Instructions:**\n"
        "Please transfer the amount via CBE or Telebirr, then send your payment receipt screenshot here!"
    )
    
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "💳 **Official Payment Details**\n\n"
        "• **Telebirr Name:** Nebyu Endashaw\n"
        "• **Telebirr Number:** `0974539791`\n\n"
        "• **CBE Account Name:** Nebyu Endashaw\n"
        "• **CBE Account Number:** `1000724373686`\n\n"
        "📸 Once you complete the transfer, **send a screenshot of the receipt** right here in our chat so our admins can verify and approve your access!"
    )
    await query.message.reply_text(text, parse_mode="Markdown")

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    
    if user_id not in pending_selections:
        await update.message.reply_text("⚠️ Please select your grade package first using /start before sending payment proof.")
        return

    package = pending_selections[user_id]
    
    # Forward the screenshot to the admin review group with approve/reject buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ])
    
    # Using plain text caption (no parse_mode) to prevent Markdown parsing errors
    caption = (
        "🔔 New Payment Verification Request!\n\n"
        f"👤 User: {user.full_name} (@{user.username or 'None'})\n"
        f"🆔 User ID: {user_id}\n"
        f"📦 Requested Package: {package}"
    )
    
    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        reply_markup=keyboard
    )
    
    await update.message.reply_text("✅ Your payment screenshot has been submitted! We will verify it shortly.")

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, target_user_id = data.split("_")
    target_user_id = int(target_user_id)
    
    if action == "approve":
        package_name = pending_selections.get(target_user_id, "Selected Package")
        approved_users[target_user_id] = package_name
        
        # Notify student
        portal_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Open NB Exam Portal", web_app=WebAppInfo(url=MINI_APP_URL))]
        ])
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 **Payment Approved!** You now have full access to **{package_name}**.\n\nClick below to start practicing:",
            reply_markup=portal_keyboard,
            parse_mode="Markdown"
        )
        await query.message.edit_caption(caption=query.message.caption + "\n\n✅ **APPROVED**", parse_mode="Markdown")
        
    elif action == "reject":
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ **Payment Rejected.** Your receipt could not be verified. Please contact support or re-submit a clear screenshot."
        )
        await query.message.edit_caption(caption=query.message.caption + "\n\n❌ **REJECTED**", parse_mode="Markdown")

# --- Main Initialization ---
if __name__ == "__main__":
    # Start Flask server in a background thread for Render's port requirement
    threading.Thread(target=run_web, daemon=True).start()

    # Build and run Telegram Bot polling
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(grade_selection, pattern="^select_"))
    app.add_handler(CallbackQueryHandler(payment_info, pattern="^pay_info$"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(approve|reject)_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_screenshot))

    print("Bot is running and polling...")
    app.run_polling()
