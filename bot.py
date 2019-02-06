try:
    from telegram.ext import Updater
    import feedparser, html2text, json, datetime
    from loguru import logger
except ImportError as err:
    print(f"Failed to import required modules: {err}")


def date_title(file_name, object_name, date_title):
    """Set the date/title of latest post from a source.
    file_name: File name to open.
    Object_name: Name of the object: feed name or twitter screen name.
    date_title: Date/title of the object being posted."""
    try:
        with open(file_name, "r+") as data_file:
            # Load json structure into memory.
            items = json.load(data_file)
            for name, data in items.items():
                if ((name) == (object_name)):
                    # Replace value of date/title with date_title
                    data["date_title"] = date_title
                    # Go to the top of feeds.json file.
                    data_file.seek(0)
                    # Dump the new json structure to the file.
                    json.dump(items, data_file, indent=2)
                    data_file.truncate()
            data_file.close()
    except IOError:
        logger.debug("date_title(): Failed to open requested file.")


def feed_to_md(state, name, feed_data):
    """A Function for converting rss feeds into markdown text.
    state: Either `set` or `None`: To execute date_title()
    name: Name of RSS feed object: eg: hacker_news
    feed_data: Data of the feed: URL and post_date from feeds.json"""
    # Parse rss feed.
    d = feedparser.parse(feed_data["url"])
    # Target the first post.
    first_post = d["entries"][0]
    title = first_post["title"]
    summary = first_post["summary"]
    post_date = first_post["published"]
    link = first_post["link"]
    h = html2text.HTML2Text()
    h.ignore_images = True
    h.ignore_links = True
    summary = h.handle(summary)
    if ((state) == ("set")):
        logger.debug(f"Running date_title for feeds.json at {datetime.datetime.now()}")
        date_title("feeds.json", name, title)
    results = []
    result = {"title": title, "summary": summary,
                "url": link, "post_date": post_date}
    results.append(result)
    # A list containing the dict object result.
    return results


def file_reader(path, mode):
    """Loads json data from path specified.
    path: Path to target_file.
    mode: Mode for file to be opened in."""
    try:
        with open(path, mode) as target_file:
            data = json.load(target_file)
            target_file.close()
            return data
    except IOError:
        logger.debug(f"Failed to open {path}")


def check_feeds(bot, job):
    """Checks the provided feeds from feeds.json for a new post."""
    logger.debug("Checking Feeds...")
    feeds = file_reader("feeds.json", "r")
    for name, feed_data in feeds.items():
        results = feed_to_md(None, name, feed_data)
        # Checking if title is the same as title in feeds.json file.
        # If the same, pass; do nothing.
        if ((feed_data["date_title"]) == (results[0]["title"])):
            pass
        elif ((feed_data["date_title"]) != (results[0]["title"])):
            results = feed_to_md("set", name, feed_data)
            logger.debug(f"Running feed_to_md at {datetime.datetime.now()}")
            rss_msg = f"""[{results[0]["title"]}]({results[0]["url"]})"""
            bot.send_message(chat_id="Insert User ID Here.", text=rss_msg, parse_mode="Markdown")
    logger.debug("Sleeping for 30 mins...")


def error(bot, update, error):
    """Log errors which occur."""
    logger.debug(error)


if __name__ == "__main__":
    # Init logging.
    logger.start("file_{time}.log", rotation="300 MB")
    # Setup Updater for Bot.
    updater = Updater(token='Insert Bot Token Here.')
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # log all errors
    dp.add_error_handler(error)
    # Run Job every 30 mins.
    j = updater.job_queue
    job_thirty_min = j.run_repeating(check_feeds, interval=1800, first=0)
    # Begin running Bot.
    updater.start_polling()