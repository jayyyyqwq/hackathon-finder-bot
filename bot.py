# bot.py
# Main Telegram bot entrypoint for Hackathon Finder

import os
import json
from pathlib import Path
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---- CONFIG ----
BOT_TOKEN = os.environ.get("HF_BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
CHAT_ID = os.environ.get("HF_CHAT_ID", "7791469095")

# where the scraper will save JSON snapshot
DATA_FILE = Path("data.json")

# ---- imports from local modules ----
try:
    from scrapers import scrape_all, SITES_INFO
    from utils import format_message, save_json, load_json, filter_by_light_rules
except Exception as e:
    scrape_all = None
    SITES_INFO = {}
    format_message = None
    save_json = None
    load_json = None
    filter_by_light_rules = None


# ---- TELEGRAM COMMANDS ----
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Hackathon Finder Bot*\n\n"
        "Commands:\n"
        "/check - run scrapers now and get fresh results\n"
        "/file  - download the raw JSON results file\n"
        "/help  - list commands\n\n"
        "Bot also runs an initial scrape automatically on startup."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/check, /file, /help")


async def cmd_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA_FILE.exists():
        await update.message.reply_text("No data file available. Run /check first.")
        return

    await update.message.reply_document(open(DATA_FILE, "rb"), filename=str(DATA_FILE.name))


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if scrape_all is None or format_message is None:
        await update.message.reply_text("Scrapers not installed yet. Wait for setup.")
        return

    await update.message.reply_text("⏳ Running scraper — please wait a few seconds...")

    results = scrape_all()
    results = filter_by_light_rules(results)
    save_json(DATA_FILE, results)

    msg = format_message(results)

    if len(msg) < 3800:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await update.message.reply_document(open(DATA_FILE, "rb"), filename=str(DATA_FILE.name))


# ---- INITIAL SCRAPE ----
def initial_scrape_and_notify(app):
    if scrape_all is None or format_message is None:
        print("scrapers/utils not ready. Skipping initial scrape.")
        return

    try:
        results = scrape_all()
        results = filter_by_light_rules(results)
        save_json(DATA_FILE, results)

        msg = format_message(results)

        app.bot.send_message(
            chat_id=int(CHAT_ID),
            text=msg,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        print("Initial scrape completed and message sent.")
    except Exception as ex:
        print("Initial scrape failed:", ex)


# ---- MAIN ----
def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        print("WARNING: BOT_TOKEN not set. Edit bot.py or set HF_BOT_TOKEN env var.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("file", cmd_file))

    print("Bot starting. It will perform an initial scrape and then listen for commands.")

    try:
        initial_scrape_and_notify(app)
    except Exception as e:
        print("Initial notify skipped:", e)

    app.run_polling()


if __name__ == "__main__":
    main()
