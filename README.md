# RSS_Feederbot [Telegram]

A Telegram bot for reading RSS Feeds.

Checks every 30 mins for news based on the user's chosen RSS feeds.

## Dependencies

Install dependencies using [requirements.txt](requirements.txt): `pip install -r requirements.txt`

## Prerequisites

1. Insert your user's chat ID found in [bot.py](bot.py):

    - You can find your chat ID using [@userinfobot](https://telegram.me/userinfobot)

    ```
    bot.send_message(chat_id="Insert user ID here.", text=rss_msg, parse_mode="Markdown")
    ```

2. Provide your bot token to the Updater class object's token parameter found in [bot.py](bot.py):

    ```
    updater = Updater(token="Insert bot token here.", use_context=True)
    ```

3. Execute bot.py.

### Container

* Ensure you run these commands from inside this directory.

* Complete the prerequisites before running these commands.

To run inside a container, run the following commands: 

1. `sudo podman build -t rss_feederbot .`

2. `sudo podman run --rm -t rss_feederbot`

## Authors -- Contributors

* **Dextroz** - *Author* - [Dextroz](https://github.com/Dextroz)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.