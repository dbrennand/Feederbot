from reader import make_reader, Reader, Entry, FeedExistsError, FeedNotFoundError
from contextlib import closing
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler
from loguru import logger
import os


class RSS_Feederbot(object):
    """
    Class for RSS_Feederbot.
    """

    def __init__(self):
        # Create log file
        logger.add(
            "rss_feederbot_{time}.log",
            format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        )
        # Setup Updater for RSS_Feederbot
        self.updater = Updater(token=os.environ["BOT_TOKEN"], use_context=True)
        # Create dictionary to compare latest RSS feed(s) entry title
        self.feeds_last_entry_title = {}

    def error_handler(self, update: Update, context: CallbackContext) -> None:
        """
        Log the error for debugging purposes.
        """
        logger.debug(f"Update: {update}\nError: {context.error}.")

    def check_feeds(self, context: CallbackContext) -> None:
        """
        Background task to check RSS feed(s) for new content and send to the user on a repeated interval.
        """
        # Update RSS feed(s)
        logger.debug("Updating RSS feeds.")
        # Use Reader object
        with closing(make_reader("db.sqlite")) as reader:
            reader.update_feeds(workers=10)
            # Retrieve all feed(s)
            logger.debug("Retrieving RSS feeds.")
            feeds = reader.get_feeds(sort="added")
            for feed in feeds:
                logger.debug(f"Checking if feed: {feed.title} has updated.")
                # Retrieve latest feed entry
                latest_entry = list(reader.get_entries(feed=feed, sort="recent"))[0]
                # Retrieve last known entry title for feed
                feed_last_title = self.feeds_last_entry_title.get(feed.title, None)
                # Compare last update title with latest RSS feed entry's title
                # If differ ent, feed has updated
                # Update the dictionary and send message of new entry
                if latest_entry.title != feed_last_title:
                    logger.debug(
                        f"Feed has a new entry.\nPrevious title was: {feed_last_title} and new title is: {latest_entry.title}\nUpdating dictionary with new title and sending update..."
                    )
                    # Create Telegram message string
                    message = f"[{latest_entry.title}]({latest_entry.link})"
                    # Update dictionary with new title
                    self.feeds_last_entry_title[feed.title] = latest_entry.title
                    # Send Telegram message
                    context.bot.send_message(
                        chat_id=self.user_chat_id, text=message, parse_mode="Markdown"
                    )
                else:
                    logger.debug(
                        f"Feed: {feed.title} does not have a new entry. Checking next feed..."
                    )
        logger.debug("All feeds checked. Waiting for next run...")

    def start(self, update: Update, context: CallbackContext) -> None:
        """
        Begin running Job to check RSS feed.

        Command args (required):
            * Feed URL: The URL of the initial feed to get updates for.
            * Interval: The interval in seconds to run the update Job on.
        """
        # Retrieve RSS feed URL provided to begin
        try:
            feed_url = str(context.args[0])
            interval = int(context.args[1])
            logger.debug(f"RSS feed URL: {feed_url}, interval: {interval}.")
        except IndexError:
            update.message.reply_text("Provide a feed URL and interval to /start.")
            return
        # Use Reader object
        # Add initial RSS feed URL to the Reader
        # Begin running the Job immediately
        with closing(make_reader("db.sqlite")) as reader:
            try:
                reader.add_feed(feed_url)
                context.job_queue.run_repeating(
                    self.check_feeds,
                    interval=interval,
                    first=0.1,
                )
                # Set user's chat ID to be used in Job
                self.user_chat_id = update.message.from_user.id
                logger.debug(f"Starting background Job to check RSS feed: {feed_url}")
                update.message.reply_text(
                    f"Background Job starting to check RSS feed: {feed_url}."
                )
            except FeedExistsError as err:
                logger.debug(f"Feed already exists: {err}.")
                update.message.reply_text(
                    f"The feed URL: {feed_url} already exists. You most likely have already ran /start."
                )

    def manage_feed(self, update: Update, context: CallbackContext) -> None:
        """
        Adds or removes a RSS feed.

        Command args (required):
            * Option: Can be either 'Add' or 'Remove'.
            * Feed URL: The URL of the RSS feed to add or remove.
        """
        # Retrieve option and RSS feed URL
        try:
            option = context.args[0]
            feed_url = context.args[1]
            logger.debug(f"Option: {option}, RSS feed URL: {feed_url}.")
        except IndexError as err:
            logger.debug(
                f"Failed to retrieve option and feed URL for /managefeed: {err}."
            )
            update.message.reply_text(
                "Provide a option and feed URL to /managefeed.\nOption can be either Add or Remove."
            )
        # Use Reader object
        with closing(make_reader("db.sqlite")) as reader:
            # Check if a RSS feed is being added or removed
            if option.lower() == "add":
                try:
                    reader.add_feed(feed_url)
                    logger.debug(f"Successfully added RSS feed: {feed_url}.")
                    update.message.reply_text(
                        f"The RSS feed: {feed_url} was successfully added."
                    )
                except FeedExistsError as err:
                    logger.debug(
                        f"The RSS feed: {feed_url} has already been added: {err}."
                    )
                    update.message.reply_text(
                        f"The RSS feed: {feed_url} has already been added."
                    )
            elif option.lower() == "remove":
                try:
                    reader.remove_feed(feed_url)
                    logger.debug(f"Successfully removed RSS feed: {feed_url}.")
                    update.message.reply_text(
                        f"The RSS feed: {feed_url} was successfully removed."
                    )
                except FeedNotFoundError as err:
                    logger.debug(f"The RSS feed: {feed_url} was not found: {err}.")
                    update.message.reply_text(
                        f"The RSS feed: {feed_url} was not found.\nTry adding it using '/managefeed add https://examplefeedurl.com'."
                    )
            else:
                logger.debug(
                    f"The option: {option} provided to /managefeed was invalid."
                )
                update.message.reply_text(
                    f"The option: {option} provided was invalid. The option can be either Add or Remove."
                )

    def change_interval(self, update: Update, context: CallbackContext) -> None:
        """
        Alter the interval to check for new RSS feed entires.

        Command args (required):
            * Interval: The interval in seconds to run the update Job on.
        """
        pass

    def show_feeds() -> None:
        """
        """
        pass

    def start_bot(self) -> None:
        """
        Start RSS_Feederbot.
        """
        logger.debug("Starting RSS_Feederbot and registering commands.")
        dispatcher = self.updater.dispatcher
        # Register error handler
        dispatcher.add_error_handler(self.error_handler)
        # Register commands
        dispatcher.add_handler(CommandHandler("start", self.start, pass_args=True))
        dispatcher.add_handler(
            CommandHandler("managefeed", self.manage_feed, pass_args=True)
        )
        dispatcher.add_handler(
            CommandHandler("changeinterval", self.change_interval, pass_args=True)
        )
        # Start RSS_Feederbot
        self.updater.start_polling()
        self.updater.idle()


if __name__ == "__main__":
    __version__ = "0.0.3"
    rss_feederbot = RSS_Feederbot()
    rss_feederbot.start_bot()
