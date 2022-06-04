# Feederbot

An Atom, RSS, and JSON feed reading Telegram bot 🤖

Feederbot checks on a user configurable interval for feed updates.

## Prerequisites

1. Docker

## Supported Commands

* `/addfeeds <url> ...` - Add feeds.

* `/removefeeds <url> ...` - Remove feeds.

* `/start <inverval>` - Start reading feeds.

* `/changeinterval <interval>` - Change the feed update interval.

* `/showfeeds` - Show feeds.

* `/showjob` - Show the datetime of the next feed update job.

## Setup

1. Build the container image:

    ```bash
    docker build -t feederbot:1.0.0 .
    ```

2. Run the container:

    ```bash
    # Using the Docker volume for the reader database
    docker run -d -t -e BOT_TOKEN="<Bot Token>" -e USER_ID="<User ID>" --name feederbot feederbot:1.0.0
    # Using a bind mount for the reader database
    docker run -d -t -e BOT_TOKEN="<Bot Token>" -e USER_ID="<User ID>" -v /path/to/store/db:/usr/src/app/reader --name feederbot feederbot:1.0.0
    ```

## Authors -- Contributors

[**dbrennand**](https://github.com/dbrennand) - *Author*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) for details.
