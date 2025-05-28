"""
Telegram-side glue code.

The heavy lifting lives in core.analysis_agent – this file only parses user
input and sends back text + optional image.
"""
from telegram import Update
from telegram.ext import ContextTypes
from core import analysis_agent


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch-all text handler **and** `/query` command."""
    # Strip leading '/query' if the user used the command
    user_text = update.message.text
    if user_text.startswith("/query"):
        user_text = user_text[len("/query"):].strip()

    reply_text, plot_path = analysis_agent.answer_query(user_text)

    await update.message.reply_text(reply_text, parse_mode="Markdown")

    if plot_path:
        try:
            with open(plot_path, "rb") as img:
                await update.message.reply_photo(img)
        except Exception as exc:
            await update.message.reply_text(
                f"*(failed to send image: {exc})*", parse_mode="Markdown"
            )
