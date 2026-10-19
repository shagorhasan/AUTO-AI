import logging
import os
from telegram import Update
from telegram.constants import ChatType
from telegram.error import TelegramError
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DEFAULT_DELETE_SECONDS = int(os.getenv("DELETE_AFTER_SECONDS", "30"))
START_ENABLED = os.getenv("AUTO_DELETE_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("loud-win-zone-auto-delete")

# Runtime settings are kept in memory. A redeploy/restart resets these to env defaults.
chat_settings: dict[int, dict[str, int | bool]] = {}


def settings_for(chat_id: int) -> dict[str, int | bool]:
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {
            "enabled": START_ENABLED,
            "seconds": max(5, min(DEFAULT_DELETE_SECONDS, 86400)),
        }
    return chat_settings[chat_id]


async def is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return False
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.reply_text("এই কমান্ডটি Telegram গ্রুপে ব্যবহার করুন।")
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
    except TelegramError:
        await message.reply_text("অ্যাডমিন যাচাই করা যায়নি। বটের গ্রুপে অ্যাক্সেস আছে কি না দেখুন।")
        return False
    if member.status not in ("administrator", "creator"):
        await message.reply_text("⛔ এই কমান্ড শুধু গ্রুপ অ্যাডমিন ব্যবহার করতে পারবেন।")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "🎮 LOUD WIN ZONE Auto Delete Bot চালু আছে।\n\n"
            "গ্রুপে আমাকে Admin করুন এবং Delete Messages অনুমতি দিন।\n"
            "/help — কমান্ড ও ব্যবহার দেখুন।"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message:
        await message.reply_text(
            "🎮 LOUD WIN ZONE — AUTO DELETE\n\n"
            "/status — বর্তমান সেটিংস\n"
            "/autodelete on — অটো ডিলিট চালু\n"
            "/autodelete off — অটো ডিলিট বন্ধ\n"
            "/settime 30 — কত সেকেন্ড পর ডিলিট হবে (৫–৮৬৪০০)\n\n"
            "🔐 সেটিংস বদলাতে গ্রুপ অ্যাডমিন হতে হবে।\n"
            "সাধারণ গ্রুপ মেসেজ নির্ধারিত সময় পর ডিলিট হবে; কমান্ড মেসেজ ও Telegram service messages বাদ।"
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.reply_text("এই কমান্ডটি গ্রুপে ব্যবহার করুন।")
        return
    cfg = settings_for(chat.id)
    await message.reply_text(
        "🎮 LOUD WIN ZONE Auto Delete Status\n"
        f"অটো ডিলিট: {'চালু ✅' if cfg['enabled'] else 'বন্ধ ⏸️'}\n"
        f"সময়: {cfg['seconds']} সেকেন্ড"
    )


async def autodelete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return
    if not await is_group_admin(update, context):
        return
    if not context.args or context.args[0].lower() not in {"on", "off"}:
        await message.reply_text("ব্যবহার: /autodelete on অথবা /autodelete off")
        return
    cfg = settings_for(chat.id)
    cfg["enabled"] = context.args[0].lower() == "on"
    await message.reply_text(
        "অটো ডিলিট চালু হয়েছে ✅" if cfg["enabled"] else "অটো ডিলিট বন্ধ হয়েছে ⏸️"
    )


async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat:
        return
    if not await is_group_admin(update, context):
        return
    if not context.args:
        await message.reply_text("ব্যবহার: /settime 30  (৫ থেকে ৮৬৪০০ সেকেন্ড)")
        return
    try:
        seconds = int(context.args[0])
    except ValueError:
        await message.reply_text("সময়টি সংখ্যায় দিন। উদাহরণ: /settime 30")
        return
    if not 5 <= seconds <= 86400:
        await message.reply_text("সময় ৫ থেকে ৮৬৪০০ সেকেন্ডের মধ্যে হতে হবে।")
        return
    cfg = settings_for(chat.id)
    cfg["seconds"] = seconds
    await message.reply_text(f"✅ ডিলিটের সময় {seconds} সেকেন্ড করা হয়েছে।")


async def delete_after_delay(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    if not job:
        return
    chat_id, message_id = job.data
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError as exc:
        # Typical causes: missing delete permission, message too old, already deleted.
        logger.info("Could not delete %s in chat %s: %s", message_id, chat_id, exc)


async def auto_delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if not message or not chat or chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    # Do not schedule commands, including commands directed at this bot.
    if message.text and message.text.startswith("/"):
        return

    cfg = settings_for(chat.id)
    if not cfg["enabled"]:
        return

    # The bot cannot delete some messages in every circumstance. Telegram permissions apply.
    seconds = int(cfg["seconds"])
    context.job_queue.run_once(
        delete_after_delay,
        when=seconds,
        data=(chat.id, message.message_id),
        name=f"delete:{chat.id}:{message.message_id}",
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is required.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("autodelete", autodelete_command))
    app.add_handler(CommandHandler("settime", settime_command))

    # All regular group messages (text, photos, documents, stickers, etc.).
    # Command messages are filtered out in the handler.
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL,
            auto_delete_message,
        )
    )

    logger.info("Starting LOUD WIN ZONE Auto Delete Bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)


if __name__ == "__main__":
    main()
