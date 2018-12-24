try:
    import feedparser, html2text, asyncio, json, datetime, telepot
    from loguru import logger
    from telepot.aio.loop import MessageLoop
    from telepot.aio.delegate import per_chat_id, create_open, pave_event_space
except ImportError:
    print("Failed to import required modules.")


class RSS(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(RSS, self).__init__(*args, **kwargs)

    async def date_title(self, file_name, object_name, date_title: str):
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

    async def feed_to_md(self, state, name, feed_data):
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
            # date_title() see utils.py
            await self.date_title("feeds.json", name, title)
        results = []
        result = {"title": title, "summary": summary,
                  "url": link, "post_date": post_date}
        results.append(result)
        # A list containing the dict object result.
        return results

    async def file_reader(self, path, mode):
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

    async def on_chat_message(self, msg):
        if msg["text"] == "/start":
            logger.start("file_{time}.log", rotation="300 MB")
            # Run forever.
            while True:
                logger.debug("Checking Feeds!")
                feeds = await self.file_reader("feeds.json", "r")

                for name, feed_data in feeds.items():
                    results = await self.feed_to_md(None, name, feed_data)
                    # Checking if title is the same as title in feeds.json file.
                    # If the same, pass; do nothing.
                    if ((feed_data["date_title"]) == (results[0]["title"])):
                        pass
                    elif ((feed_data["date_title"]) != (results[0]["title"])):
                        results = await self.feed_to_md("set", name, feed_data)
                        logger.debug(f"Running feed_to_md at {datetime.datetime.now()}")
                        rss_msg = f"""[{results[0]["title"]}]({results[0]["url"]})"""
                        await self.bot.sendMessage(msg["chat"]["id"], rss_msg, parse_mode="Markdown")
                # Sleep for 30 mins before re-checking.
                logger.debug("Sleeping for 30 mins.")
                await asyncio.sleep(1800)


if __name__ == "__main__":
    TOKEN = "Insert Token Here."
    bot = telepot.aio.DelegatorBot(TOKEN, [
        pave_event_space()(
            per_chat_id(), create_open, RSS, timeout=10),
    ])

    loop = asyncio.get_event_loop()
    loop.create_task(MessageLoop(bot).run_forever())
    print('Listening ...')

    loop.run_forever()
