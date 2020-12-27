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
            logger.debug("Retrieving RSS feed(s).")
            feeds = reader.get_feeds(sort="added")
            for feed in feeds:
                logger.debug(f"Checking if RSS feed: {feed.title} has updated.")
                # Retrieve latest feed entry
                latest_entry = list(reader.get_entries(feed=feed, sort="recent"))[0]
                # Retrieve last known entry title for feed
                feed_last_title = self.feeds_last_entry_title.get(feed.title, None)
                # Compare last update title with latest RSS feed entry's title
                # If different, feed has updated
                # Update the dictionary and send message of new entry
                if latest_entry.title != feed_last_title:
                    logger.debug(
                        f"RSS feed: {feed.title} has a new entry.\nPrevious title was: {feed_last_title} and new title is: {latest_entry.title}\nUpdating dictionary with new title and sending update..."
                    )
                    # Create Telegram message string
                    message = f"[{latest_entry.title}]({latest_entry.link})"
                    # Update dictionary with new title
                    self.feeds_last_entry_title[feed.title] = latest_entry.title
                    logger.debug(self.feeds_last_entry_title)
                    # Send Telegram message
                    context.bot.send_message(
                        chat_id=self.user_id, text=message, parse_mode="Markdown"
                    )
                else:
                    logger.debug(
                        f"Feed: {feed.title} does not have a new entry. Checking next RSS feed..."
                    )
        logger.debug("All RSS feeds checked. Waiting for next run...")

    def start(self, update: Update, context: CallbackContext) -> None:
        """
        Begin running the background Job to check RSS feeds.

        Command args (required):
            * Feed URL: The URL of the initial feed to get updates for.
            * Interval: The interval in seconds to run the background Job on.
        """
        # Retrieve RSS feed URL provided to begin
        try:
            feed_url = str(context.args[0])
            interval = int(context.args[1])
            logger.debug(f"RSS feed URL: {feed_url}, interval: {interval}.")
        except IndexError as err:
            logger.debug(f"Failed to retrieve RSS feed URL and interval: {err}.")
            update.message.reply_text("Provide an RSS feed URL and interval to /start.")
            return
        # Use Reader object
        # Add initial RSS feed URL to the Reader
        # Begin running the background Job immediately
        with closing(make_reader("db.sqlite")) as reader:
            try:
                logger.debug(f"Attempting to add RSS feed: {feed_url}.")
                reader.add_feed(feed_url)
            except FeedExistsError as err:
                logger.debug(f"RSS feed already exists: {err}.")
                update.message.reply_text(
                    f"The RSS feed URL: {feed_url} already exists. You most have already ran /start."
                )
                return
            logger.debug(f"Starting background Job to check RSS feed: {feed_url}.")
            # Set user's ID to be used in the background Job
            self.user_id = update.message.from_user.id
            logger.debug(f"User's ID: {self.user_id}.")
            job = context.job_queue.run_repeating(
                self.check_feeds, interval=interval, name="check_feeds"
            )
            job.run(context.dispatcher)

    def manage_feed(self, update: Update, context: CallbackContext) -> None:
        """
        Adds or removes an RSS feed.

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
                f"Failed to retrieve option and RSS feed URL for /managefeed: {err}."
            )
            update.message.reply_text(
                "Provide an option and RSS feed URL to /managefeed.\nOption can be either Add or Remove."
            )
            return
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

    def show_feeds(self, update: Update, context: CallbackContext) -> None:
        """
        Show RSS feed(s) currently being checked for updates.
        """
        # Use Reader object
        with closing(make_reader("db.sqlite")) as reader:
            # Obtain RSS feed(s) currently being checked for updates
            feeds = list(reader.get_feeds(sort="added"))
        update.message.reply_text(
            f"RSS feeds being checked for updates: {[feed.url for feed in feeds]}."
        )

    def change_interval(self, update: Update, context: CallbackContext) -> None:
        """
        Alter the interval to check for new RSS feed entires.

        Command args (required):
            * Interval: The interval in seconds to run the background Job on.
        """
        # Retrieve interval
        try:
            interval = int(context.args[0])
            logger.debug(f"Interval: {interval}.")
        except IndexError as err:
            logger.debug(f"Failed to retrieve interval /changeinterval: {err}.")
            update.message.reply_text("Provide an interval to /changeinterval.")
            return
        # Remove the previous background Job
        try:
            logger.debug(f"Attempting to remove previous background Job.")
            for job in context.job_queue.get_jobs_by_name("check_feeds"):
                job.schedule_removal()
            logger.debug("Successfully removed previous background Job.")
        except:  # TODO: Find out what exception occurs here
            logger.debug("Failed to remove previous background Job.")
            update.message.reply_text(
                "Failed to remove previous background Job. Have your ran /start?"
            )
            return
        # Create a new background Job using provided interval
        logger.debug(
            f"Attemping to create new background Job with a {interval} second interval."
        )
        context.job_queue.run_repeating(
            self.check_feeds, interval=interval, name="check_feeds"
        )
        logger.debug(f"Successfully created new background Job.")
        update.message.reply_text(
            f"Successfully created new background Job with a {interval} second interval."
        )

    def show_job(self, update: Update, context: CallbackContext) -> None:
        """
        Utility function to show the currently running background Job(s), if any.
        """
        jobs = list(context.job_queue.jobs())
        for job in jobs:
            logger.debug(
                f"Background Job: {job.name} next run is on: {job.next_t.strftime('%m/%d/%Y, %H:%M:%S')}"
            )
        update.message.reply_text(
            f"Background Job(s) currently running are: {[job.name for job in jobs]}"
        )

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
            CommandHandler("showfeed", self.show_feeds, pass_args=True)
        )
        dispatcher.add_handler(
            CommandHandler(
                "changeinterval",
                self.change_interval,
                pass_args=True,
                pass_job_queue=True,
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "showjob",
                self.show_job,
                pass_job_queue=True,
            )
        )
        # Start RSS_Feederbot
        self.updater.start_polling()
        self.updater.idle()


if __name__ == "__main__":
    __version__ = "0.0.3"
    rss_feederbot = RSS_Feederbot()
    rss_feederbot.start_bot()
