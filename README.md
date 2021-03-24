# RSS_Feederbot [Telegram]

A Telegram bot for reading RSS Feeds.

Checks on an interval for RSS feed updates.

## Setup

### Normal

1. Install dependencies from [requirements.txt](requirements.txt) using: `pip install -r requirements.txt`

2. Set the bot token environment variable:

    PowerShell: `$Env:BOT_TOKEN = "Insert bot token here."`

    Bash: `export BOT_TOKEN="Insert bot token here."`

3. Run bot.py.

### Docker

> [!NOTE]
> Run the following commands from inside the project directory.

1. `docker build -t rss_feederbot:0.0.4 .`

2. `docker run --rm --name rss_feederbot -e BOT_TOKEN="Insert bot token here." -d -t rss_feederbot:0.0.4`

## Usage

Add and remove RSS feeds using the `/managefeed` command:

* Add: `/managefeed add https://examplefeedurl.com`

* Remove: `/managefeed remove https://examplefeedurl.com`

Begin checking for RSS feed updates using the `/start` command, providing an interval (in seconds) for how often to check for updates:

> [!NOTE]
> The example below is every 30 minutes (Highly recommended).

`/start 1800`

If you decide that you want to change the interval of how often the bot checks for RSS feed updates, you can use the `/changeinterval` command, providing the new interval (in seconds):

> [!NOTE]
> The example below is every hour.

`/changeinterval 3600`

To see the RSS feed(s) currently being checked for updates, use the `/showfeed` command.

To see when the bot will next check for RSS feed updates, use the `/showjob` command.

## Authors -- Contributors

* **dbrennand** - *Author* - [dbrennand](https://github.com/dbrennand)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.
