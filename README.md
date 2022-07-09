# Feederbot

An Atom, RSS, and JSON feed reading Telegram bot 🤖

Feederbot checks on a user configurable interval for feed updates.

## Prerequisites

1. A Telegram bot token from [@BotFather](https://t.me/botfather)

2. Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

3. Docker

## Supported Commands

* `/addfeeds <url> ...` - Add feeds.

* `/removefeeds <url> ...` - Remove feeds.

* `/start <interval>` - Start reading feeds.

* `/changeinterval <interval>` - Change the feed update interval.

* `/showfeeds` - Show feeds.

* `/showjob` - Show the datetime of the next feed update job.

## Setup

1. Build the container image:

    ```bash
    # Using docker-compose
    docker-compose build
    # Using docker build
    docker build -t feederbot:1.0.1 .
    ```

2. Run the container:

    ```bash
    # Using docker-compose
    docker-compose up -d
    # Using the Docker volume for the reader database
    docker run -d -t -e BOT_TOKEN="<Bot Token>" -e USER_ID="<User ID>" --name feederbot feederbot:1.0.1
    # Using a bind mount for the reader database
    docker run -d -t -e BOT_TOKEN="<Bot Token>" -e USER_ID="<User ID>" -v /path/to/store/db:/usr/src/app/reader --name feederbot feederbot:1.0.1
    ```

## Authors -- Contributors

[**dbrennand**](https://github.com/dbrennand) - *Author*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.
