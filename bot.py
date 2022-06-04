from typing import List
from loguru import logger
import reader as r
import contextlib
import os
import sys
import emoji
import telegram
import telegram.ext

READER_DB_PATH = "/usr/src/app/reader/db.sqlite"
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_ID = os.environ["USER_ID"]
CHECK_MARK_EMOJI = emoji.emojize(":check_mark_button:", language="alias")
CROSS_MARK_EMOJI = emoji.emojize(":x:", language="alias")
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {extra[function]} | {message}",
    enqueue=True,
)


async def error_handler(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Error handler.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.
    """
    logger.error(f"{CROSS_MARK_EMOJI} {context.error}: {update}")


async def check_feeds(context: telegram.ext.CallbackContext.DEFAULT_TYPE) -> None:
    """Check for feed updates.

    Args:
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.
    """
    context_logger = logger.bind(function="check_feeds")
    context_logger.info(f"{CHECK_MARK_EMOJI} Checking for feed updates.")
    with contextlib.closing(r.make_reader(READER_DB_PATH)) as reader:
        reader.update_feeds(workers=10)
        context_logger.info(f"{CHECK_MARK_EMOJI} Feeds updated.")
        for feed in reader.get_feeds(sort="added"):
            context_logger.info(f"{CHECK_MARK_EMOJI} Checking {feed.title}.")
            # Get all feed entries
            entries = list(reader.get_entries(feed=feed, sort="recent"))
            # Get unread feed entries
            unread_entires = list(
                reader.get_entries(feed=feed, sort="recent", read=False)
            )
            entries_count = len(entries)
            unread_entires_count = len(unread_entires)
            if unread_entires:
                # If this is a newly added feed, all of the entries will be unread
                # so we need to check if the unread feed entry count is identical to the
                # total feed entry count
                if unread_entires_count == entries_count:
                    context_logger.info(
                        f"{CHECK_MARK_EMOJI} Unread entries identical to total entries for {feed.title}."
                    )
                    # This is likely a newly added feed so send the 5 most recent entries
                    await send_feed_entries(context, feed.title, unread_entires[:5])
                else:
                    context_logger.info(
                        f"{CHECK_MARK_EMOJI} {unread_entires_count} new entries for {feed.title}."
                    )
                    await send_feed_entries(context, feed.title, unread_entires)
                # Mark entries as read
                for entry in unread_entires:
                    reader.mark_entry_as_read(entry)
                context_logger.info(
                    f"{CHECK_MARK_EMOJI} {unread_entires_count} entries marked as read for {feed.title}."
                )
            else:
                context_logger.info(
                    f"{CHECK_MARK_EMOJI} No new entries for {feed.title}."
                )


async def send_feed_entries(
    context: telegram.ext.CallbackContext.DEFAULT_TYPE,
    feed_title: str,
    entries: List[r.Entry],
) -> None:
    """Send feed entries.

    Args:
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.
        feed_title (str): The title of the feed.
        entries (Iterable[r.Entry]): Feed entries to send.
    """
    context_logger = logger.bind(function="send_feed_entries")
    context_logger.info(
        f"{CHECK_MARK_EMOJI} Sending {len(entries)} entries for {feed_title}."
    )
    fmt_entries = [(entry.title, entry.link) for entry in entries]
    msg = "{0}\n\n{1}".format(
        feed_title, "\n".join(f"[{title}]({link})" for title, link in fmt_entries)
    )
    await context.bot.send_message(
        chat_id=USER_ID,
        text=msg,
        parse_mode="Markdown",
    )


async def add_feeds(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Add feeds.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.

    Command Args:
        url (str): The URL of the feed to add.
    """
    context_logger = logger.bind(function="add_feed")
    feeds = context.args
    context_logger.info(f"{CHECK_MARK_EMOJI} Adding {len(feeds)} feeds.")
    with contextlib.closing(r.make_reader(READER_DB_PATH)) as reader:
        for feed in feeds:
            try:
                reader.add_feed(feed)
                context_logger.info(f"{CHECK_MARK_EMOJI} Added {feed}.")
                await update.message.reply_text(f"{CHECK_MARK_EMOJI} Added {feed}.")
            except r.FeedExistsError:
                context_logger.error(f"{CROSS_MARK_EMOJI} Feed {feed} already exists.")
                await update.message.reply_text(
                    f"{CROSS_MARK_EMOJI} Feed {feed} already exists."
                )


async def remove_feeds(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Remove feeds.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.

    Command Args:
        url (str): The URL of the feed to remove.
    """
    context_logger = logger.bind(function="remove_feed")
    feeds = context.args
    context_logger.info(f"{CHECK_MARK_EMOJI} Removing {len(feeds)} feeds.")
    with contextlib.closing(r.make_reader(READER_DB_PATH)) as reader:
        for feed in feeds:
            try:
                reader.delete_feed(feed)
                context_logger.info(f"{CHECK_MARK_EMOJI} Removed {feed}.")
                await update.message.reply_text(f"{CHECK_MARK_EMOJI} Removed {feed}.")
            except r.FeedNotFoundError:
                context_logger.error(f"{CROSS_MARK_EMOJI} Feed {feed} does not exist.")
                await update.message.reply_text(
                    f"{CROSS_MARK_EMOJI} Feed {feed} does not exist."
                )


async def change_interval(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Change the feed update interval.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.

    Command Args:
        interval (int): The interval in seconds to check for feed updates.
    """
    context_logger = logger.bind(function="change_interval")
    try:
        interval = int(context.args[0])
        context_logger.info(
            f"{CHECK_MARK_EMOJI} Changing feed(s) job - Interval: {interval}"
        )
        jobs = context.job_queue.jobs()
        if jobs:
            for job in jobs:
                job.schedule_removal()
            context.job_queue.run_repeating(check_feeds, interval=interval)
            context_logger.info(f"{CHECK_MARK_EMOJI} Changed feed(s) job.")
            await update.message.reply_text(f"{CHECK_MARK_EMOJI} Changed feed(s) job.")
        else:
            context_logger.error(f"{CROSS_MARK_EMOJI} No feed(s) job found.")
            await update.message.reply_text(f"{CROSS_MARK_EMOJI} No feed(s) job found.")
    except IndexError:
        context_logger.error(f"{CROSS_MARK_EMOJI} Interval missing.")
        await update.message.reply_text(f"{CROSS_MARK_EMOJI} Interval missing.")


async def show_feeds(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Show feeds.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.
    """
    context_logger = logger.bind(function="show_feeds")
    context_logger.info(f"{CHECK_MARK_EMOJI} Showing feeds.")
    with contextlib.closing(r.make_reader(READER_DB_PATH)) as reader:
        feeds = list(reader.get_feeds(sort="added"))
        feed_count = len(feeds)
        context_logger.info(f"{CHECK_MARK_EMOJI} Found {feed_count} feeds.")
        context_logger.info(
            f"{CHECK_MARK_EMOJI} {feed_count} feeds: {[feed.url for feed in feeds]}."
        )
        await update.message.reply_text(
            f"{CHECK_MARK_EMOJI} {feed_count} feeds: {[feed.url for feed in feeds]}."
        )


async def show_job(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Show the datetime of the next feed update job.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.
    """
    context_logger = logger.bind(function="show_job")
    context_logger.info(f"{CHECK_MARK_EMOJI} Showing feed(s) job.")
    jobs = context.job_queue.jobs()
    for job in jobs:
        context_logger.info(
            f"{CHECK_MARK_EMOJI} Feed(s) job: {job.name} next run is {job.next_t.strftime('%m/%d/%Y, %H:%M:%S UTC')}."
        )
        await update.message.reply_text(
            f"{CHECK_MARK_EMOJI} Feed(s) job: {job.name} next run is {job.next_t.strftime('%m/%d/%Y, %H:%M:%S UTC')}"
        )


async def start(
    update: telegram.Update, context: telegram.ext.CallbackContext.DEFAULT_TYPE
) -> None:
    """Start reading feeds.

    Starts the background job to read feeds on an interval.

    Args:
        update (telegram.Update): Object representing the incoming update from Telegram.
        context (telegram.ext.CallbackContext.DEFAULT_TYPE): Object representing the callback context.

    Command Args:
        interval (int): The interval in seconds to check for feed updates.
    """
    context_logger = logger.bind(function="start")
    try:
        interval = int(context.args[0])
        context_logger.info(
            f"{CHECK_MARK_EMOJI} Starting feed(s) job - Interval: {interval}"
        )
        context.job_queue.run_repeating(check_feeds, interval=interval, first=1)
        context_logger.info(f"{CHECK_MARK_EMOJI} Started feed(s) job.")
        await update.message.reply_text(f"{CHECK_MARK_EMOJI} Started feed(s) job.")
    except IndexError:
        context_logger.error(f"{CROSS_MARK_EMOJI} Interval missing.")
        await update.message.reply_text(f"{CROSS_MARK_EMOJI} Interval missing.")


app = telegram.ext.ApplicationBuilder().token(BOT_TOKEN).build()
app.add_error_handler(error_handler)
app.add_handler(telegram.ext.CommandHandler("start", start))
app.add_handler(telegram.ext.CommandHandler("addfeeds", add_feeds))
app.add_handler(telegram.ext.CommandHandler("removefeeds", remove_feeds))
app.add_handler(telegram.ext.CommandHandler("changeinterval", change_interval))
app.add_handler(telegram.ext.CommandHandler("showfeeds", show_feeds))
app.add_handler(telegram.ext.CommandHandler("showjob", show_job))
app.run_polling()
