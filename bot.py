try:
    from telegram.ext import Updater
    import feedparser, html2text, json, datetime
    from loguru import logger
except ImportError as err:
    raise ImportError(f"Failed to import required modules: {err}")


def date_title(file_name: str, object_name: str, date_title: str):
    """
    Set the date/title of latest post from a source.
    :param file_name: The name of the file to open.
    :param object_name: The name of the object to replace.
    :param date_title: The date/title to replace the existing object with.
    """
    try:
        with open(file_name, "r+") as data_file:
            # Load json structure into memory.
            feeds = json.load(data_file)
            for name, data in feeds.items():
                if (name) == (object_name):
                    # Replace value of date/title with date_title
                    data["date_title"] = date_title
                    # Go to the top of feeds.json file.
                    data_file.seek(0)
                    # Dump the new json structure to the file.
                    json.dump(feeds, data_file, indent=2)
                    data_file.truncate()
    except IOError:
        logger.debug("date_title: Failed to open requested file.")


def feed_to_md(name: str, feed_data: dict):
    """
    Converts an RSS feed into markdown text.
    :param name: The name of the RSS feed. eg: hacker_news.
    :param feed_data: The data of the feed. eg: url and post_date from feeds.json.
    :rtype: A dict object containing data about the top feed item.
    """
    # Parse RSS feed.
    d = feedparser.parse(feed_data["url"])
    # Target the first post.
    first_post = d["entries"][0]
    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = True
    summary = first_post["summary"]
    summary = h.handle(summary)
    result = {
        "title": first_post["title"],
        "summary": summary,
        "url": first_post["link"],
        "post_date": first_post["published"],
    }
    return result


def file_reader(path: str, mode: str):
    """
    Loads JSON data from the file path specified.
    :param path: The path to the target file to open.
    :param mode: The mode to open the target file in.
    :rtype: JSON data from the specified file.
    """
    try:
        with open(path, mode) as target_file:
            data = json.load(target_file)
            return data
    except IOError:
        logger.debug(f"Failed to open the file: {path}")


def check_feeds(context):
    """
    Checks RSS feeds from feeds.json for a new post.
    :param context: The telegram CallbackContext class object.
    """
    logger.debug("Checking if feeds have updated...")
    feeds = file_reader("feeds.json", "r")
    for name, feed_data in feeds.items():
        logger.debug(f"Checking if feed: {name} requires updating...")
        result = feed_to_md(name, feed_data)
        # Checking if title is the same as title in feeds.json file.
        # If the same; do nothing.
        if (feed_data["date_title"]) == (result["title"]):
            logger.debug(f"Feed: {name} does not require any updates.")
            continue
        elif (feed_data["date_title"]) != (result["title"]):
            logger.debug(
                f"Feed: {name} requires updating! Running date_title for feeds.json."
            )
            date_title("feeds.json", name, result["title"])
            # Set RSS message.
            rss_msg = f"[{result['title']}]({result['url']})"
            context.bot.send_message(chat_id="Insert user ID here.", text=rss_msg, parse_mode="Markdown")
    logger.debug("Sleeping for 30 mins...")


def error(update, context):
    """
    Log errors which occur.
    :param update: The update which caused the error.
    :param context: The error which occurred.
    """
    logger.debug(f"Update: {update} caused the error: {context.error}")


if __name__ == "__main__":
    __version__ = "0.0.2"
    # Init logging.
    logger.add(
        "bot_{time}.log",
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        rotation="300 MB",
    )
    # Setup Updater for bot.
    updater = Updater(token="Insert bot token here.", use_context=True)
    # Get the dispatcher to register handlers.
    dp = updater.dispatcher
    # log all errors.
    dp.add_error_handler(error)
    # Run Job every 30 mins.
    j = updater.job_queue
    job_thirty_min = j.run_repeating(check_feeds, interval=1800, first=0)
    # Begin running the bot.
    updater.start_polling()
