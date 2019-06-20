# RSS_Feederbot [Telegram]
A Telegram bot for reading RSS Feeds.
Checks every 30 mins for news based on users chosen RSS feeds.


## Dependencies
Install requirements using Pipfile:
```
pipenv install
```

## Usage
Insert **User's Chat ID** found in [bot.py](bot.py):
```
Line 88: bot.send_message(chat_id="Insert User ID Here.", text=rss_msg, parse_mode="Markdown")
```

Insert Bot Token into **TOKEN** found in [bot.py](bot.py):
```
Line 96: updater = Updater(token='Insert Bot Token Here.')
```

## Authors -- Contributors

* **Dextroz** - *Author* - [Dextroz](https://github.com/Dextroz)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.