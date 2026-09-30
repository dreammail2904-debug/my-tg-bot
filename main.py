import json
import os
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# अपनी जानकारी यहां डालो
# =========================

TOKEN = "8774498374:AAEv_N5_Jgr_7wGRgy-Cv108veOgc3A_ZCM"
ADMIN_ID = 8641823834
UPI_ID = "ansu.pth@ptyes"

# =========================

FILE = "videos.json"

CATEGORIES = {
    "viral": "🔥 Viral Videos",
    "new": "🆕 New Videos",
    "trending": "📱 Trending Videos"
}

PRICES = [10, 20, 30, 50, 100] # Price in Rupees (₹)


def load_data():
    if not os.path.exists(FILE):
        return {"viral": [], "new": [], "trending": []}

    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"viral": [], "new": [], "trending": []}


def save_data():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


videos = load_data()
pending = {}


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🔥 Viral Videos", callback_data="cat_viral")],
        [InlineKeyboardButton("🆕 New Videos", callback_data="cat_new")],
        [InlineKeyboardButton("📱 Trending Videos", callback_data="cat_trending")]
    ]

    await update.message.reply_text(
        "🎬 Welcome!\n\n"
        "👇 Category select करें:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# MY ID
# =========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"आपकी Telegram ID:\n\n{update.effective_user.id}"
    )


# =========================
# ADMIN VIDEO RECEIVE
# =========================

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    video = update.message.video

    pending[ADMIN_ID] = {
        "file_id": video.file_id,
        "caption": update.message.caption or ""
    }

    keyboard = [
        [InlineKeyboardButton("🔥 Viral", callback_data="upload_viral")],
        [InlineKeyboardButton("🆕 New", callback_data="upload_new")],
        [InlineKeyboardButton("📱 Trending", callback_data="upload_trending")]
    ]

    await update.message.reply_text(
        "✅ Video मिल गया!\n\n"
        "अब category चुनो:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADMIN CATEGORY
# =========================

async def admin_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    category = query.data.replace("upload_", "")

    if ADMIN_ID not in pending:
        await query.edit_message_text(
            "❌ पहले video भेजो।"
        )
        return

    pending[ADMIN_ID]["category"] = category

    keyboard = []

    for price in PRICES:
        keyboard.append([
            InlineKeyboardButton(
                f"₹ {price}",
                callback_data=f"price_{price}"
            )
        ])

    await query.edit_message_text(
        f"📂 {CATEGORIES[category]}\n\n"
        "💰 Video की price चुनो:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADMIN PRICE
# =========================

async def admin_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if ADMIN_ID not in pending:
        await query.edit_message_text("❌ Session खत्म हो गया।")
        return

    price = int(query.data.replace("price_", ""))

    item = pending[ADMIN_ID]
    category = item["category"]

    video = {
        "id": str(uuid.uuid4()),
        "file_id": item["file_id"],
        "caption": item["caption"],
        "price": price,
        "title": f"Video {len(videos[category]) + 1}"
    }

    videos[category].append(video)
    save_data()

    del pending[ADMIN_ID]

    await query.edit_message_text(
        "✅ Video save हो गया!\n\n"
        f"📂 Category: {CATEGORIES[category]}\n"
        f"💰 Price: ₹{price}\n\n"
        "अब users इसे payment करके unlock कर सकते हैं."
    )


# =========================
# USER CATEGORY
# =========================

async def user_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    category = query.data.replace("cat_", "")
    items = videos.get(category, [])

    if not items:
        await query.edit_message_text(
            f"{CATEGORIES[category]}\n\n"
            "अभी कोई video नहीं है.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="menu")]
            ])
        )
        return

    buttons = []

    for item in items:
        buttons.append([
            InlineKeyboardButton(
                f"🔒 {item['title']} — ₹{item['price']}",
                callback_data=f"buy_{item['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("⬅️ Back", callback_data="menu")
    ])

    await query.edit_message_text(
        f"{CATEGORIES[category]}\n\n"
        "👇 Video चुनो:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# =========================
# MAIN MENU
# =========================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🔥 Viral Videos", callback_data="cat_viral")],
        [InlineKeyboardButton("🆕 New Videos", callback_data="cat_new")],
        [InlineKeyboardButton("📱 Trending Videos", callback_data="cat_trending")]
    ]

    await query.edit_message_text(
        "🎬 Category select करें:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BUY (UPI DETAILS)
# =========================

async def buy_video(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    video_id = query.data.replace("buy_", "")
    selected = None

    for category in videos:
        for item in videos[category]:
            if item["id"] == video_id:
                selected = item
                break
        if selected:
            break

    if not selected:
        await query.answer(
            "Video नहीं मिला.",
            show_alert=True
        )
        return

    # User ko payment ki details dikhana
    payment_msg = (
        f"🔒 **{selected['title']}** unlock करने के लिए payment करें:\n\n"
        f"💵 **Price:** ₹{selected['price']}\n"
        f"💳 **UPI ID:** `{UPI_ID}`\n\n"
        "📌 **Steps:**\n"
        "1. Upar di gayi UPI ID par ₹{selected['price']} pay karen.\n"
        "2. Payment hone ke baad Screenshot/Transaction ID ki photo is bot ko bhejein.\n"
        "3. Admin Verify karke aapko video bhej dega."
    )

    await query.edit_message_text(
        payment_msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="menu")]
        ])
    )


# =========================
# HANDLE SCREENSHOT / PAYMENT VERIFICATION
# =========================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Agar user koi screenshot/photo bhejta hai, toh yeh Admin ko forward kar dega
    user = update.effective_user
    photo = update.message.photo[-1].file_id

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve & Send Video", callback_data=f"appr_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")
        ]
    ]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=f"📩 **New Payment Proof!**\n\nUser: {user.full_name} (@{user.username})\nID: `{user.id}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ Apka payment proof receive ho gaya hai. Admin ki taraf se verify hote hi video mil jayegi.")


async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("appr_"):
        user_id = int(data.replace("appr_", ""))
        await context.bot.send_message(user_id, "✅ Payment Verified! Apka video unlock kar diya gaya hai.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ **Approved**")
    elif data.startswith("rej_"):
        user_id = int(data.replace("rej_", ""))
        await context.bot.send_message(user_id, "❌ Apka payment verify nahi ho paya. Kripya sahi screenshot bhejein.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ **Rejected**")


# =========================
# MAIN BOT RUNNER
# =========================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.add_handler(CallbackQueryHandler(admin_category, pattern="^upload_"))
    app.add_handler(CallbackQueryHandler(admin_price, pattern="^price_"))
    app.add_handler(CallbackQueryHandler(user_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(buy_video, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^(appr_|rej_)"))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
