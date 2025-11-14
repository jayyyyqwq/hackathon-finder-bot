# bot.py
# Main Telegram bot entrypoint for Hackathon Finder (Option C architecture)

import os
import json
from pathlib import Path
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---- CONFIG ----
# Put your secret token here (do NOT share it)
BOT_TOKEN = os.environ.get("HF_BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
# Put your personal chat id here (string or int). You can also set via env HF_CHAT_ID
CHAT_ID = os.environ.get("HF_CHAT_ID", "7791469095")

# where the scraper will save JSON snapshot
DATA_FILE = Path("data.json")

# ---- imports from local modules (we'll create these next) ----
# scrapers.scrape_all() -> returns dict: { source_name: [ { "title":..., "url":..., "deadline":... }, ... ] }
# utils.format_message(results) -> returns a string (telegram markdown/html) ready to send
# utils.save_json(path, results) -> saves to file
# utils.load_json(path) -> loads snapshot or {}
# utils.filter_by_deadline(results) -> returns results filtered (only active / upcoming)
try:
    from scrapers import scrape_all, SITES_INFO  # SITES_INFO optional metadata (name->url)
    from utils import format_message, save_json, load_json, filter_by_deadline
except Exception as e:
    # If these aren't present yet, we'll still let the file be created. Next step: create scrapers.py + utils.py
    scrape_all = None
    SITES_INFO = {}
    format_message = None
    save_json = None
    load_json = None
    filter_by_deadline = None


# ---- TELEGRAM HELPERS ----
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
    # run scrapers immediately and reply with results
    if scrape_all is None or format_message is None:
        await update.message.reply_text("Scrapers not installed yet. Wait for setup.")
        return

    await update.message.reply_text("⏳ Running scraper — please wait a few seconds...")

    results = scrape_all()  # dict: source -> list of items (dict with title/url/deadline)
    results = filter_by_deadline(results)  # keep only active/upcoming
    # Save snapshot
    save_json(DATA_FILE, results)

    # Create a human-friendly message
    msg = format_message(results)
    # Telegram has message length limits; if too long, we'll send as file
    if len(msg) < 3800:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        # fallback: send JSON file
        await update.message.reply_document(open(DATA_FILE, "rb"), filename=str(DATA_FILE.name))


# ---- Startup helper: run initial scrape and DM you the results ----
def initial_scrape_and_notify(app):
    """
    This is called right after the bot starts polling.
    It performs a single scrape and sends the results to your chat id.
    """
    if scrape_all is None or format_message is None:
        print("scrapers/utils not ready. Skipping initial scrape.")
        return

    try:
        results = scrape_all()
        results = filter_by_deadline(results)
        save_json(DATA_FILE, results)

        msg = format_message(results)
        # the Application object exposes a bot via app.bot
        # send to configured CHAT_ID
        app.bot.send_message(chat_id=int(CHAT_ID), text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        print("Initial scrape completed and message sent.")
    except Exception as ex:
        print("Initial scrape failed:", ex)


# ---- main ----
def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        print("WARNING: BOT_TOKEN not set. Edit bot.py or set HF_BOT_TOKEN env var.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("file", cmd_file))

    print("Bot starting. It will perform an initial scrape and then listen for commands.")
    # Use `post_init` style: run initial scrape once app is ready (before polling loop)
    # python-telegram-bot exposes running_app in run_polling; but simplest is to call initial_scrape_and_notify right before run_polling
    # We wrap in try/except so missing modules don't crash startup
    try:
        # Attach a small callback to run once app has bot available
        initial_scrape_and_notify(app)
    except Exception as e:
        print("Initial notify skipped:", e)

    # This will block and handle polling safely on Windows and other envs
    app.run_polling()


if __name__ == "__main__":
    main()
