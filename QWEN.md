# Retwitch Project Context

This directory contains the `retwitch` component of the GunlinuxBot project. It's a Python-based service responsible for interacting with the Twitch API, handling events, and sending messages to a Twitch chat. It uses Redis for message queuing.

## Project Type
**Code Project (Python)**

## Key Technologies
*   **Language:** Python (>=3.10)
*   **Dependencies:** Managed by `uv` (via `pyproject.toml`). Key libraries include `twitchio` for Twitch interaction, `coredis` for Redis, `requeue` (custom library for queuing), `commander` (custom library for commands).
*   **Build/Dev Tool:** `uv` (for dependency management, building, and running).
*   **Linting/Formatting:** `uv run ruff`
*   **Type Checking:** `uv run pyright`
*   **Testing:** `uv run pytest`

## Project Overview
The `retwitch` service is designed to:
1.  Connect to Twitch using the EventSub API to receive events (likely chat messages, channel points, follows, etc.).
2.  Process these events and push them onto a Redis queue (`settings.TWITCH_EVENTS`).
3.  Consume messages from a separate Redis queue (`settings.TWITCH_OUT`) and send them as chat messages back to Twitch.
4.  Handle specific commands received via Twitch chat, potentially executing predefined actions or scripts.

It consists of several main components:
*   **`retwitch_getter.py`**: The main process for receiving Twitch events and pushing them to the `TWITCH_EVENTS` Redis queue.
*   **`retwitch_worker.py`**: The main process for consuming events from the `TWITCH_EVENTS` queue, handling commands, and potentially sending responses to the `TWITCH_OUT` queue.
*   **`retwitch_sender.py`**: The main process for consuming messages from the `TWITCH_OUT` queue and sending them to Twitch chat.
*   **`twitch_cli.py`**: A utility script for generating OAuth URLs and saving tokens required for Twitch API access.
*   **`twitch_mssg.py`**: A utility script to push a single message directly to the `TWITCH_OUT` Redis queue.

## Configuration
Configuration is primarily handled via environment variables, likely loaded from a `.env` file (see `twitch_cli.py` and `retwitch_getter.py`). Key variables include:
*   `RECLIENT_ID`: Twitch application Client ID.
*   `RECLIENT_SECRET`: Twitch application Client Secret.
*   `REOWNER_ID`: Twitch User ID of the broadcaster.
*   `REBOT_ID`: Twitch User ID of the bot user.
*   `REDIS_URL`: URL for the main Redis instance (used for events and outgoing messages).
*   `TWITCH_REDIS_URL`: URL for a specific Redis instance for Twitch interactions (if different).

Settings for queue names, token files, command directories, etc., are imported from `retwitch.settings` and `gunlinuxbot.settings`.

## Building and Running
The `Makefile` provides convenient commands for development tasks. Assuming `uv` is installed:

*   **Install Dependencies (including dev):** `make dev` (runs `uv sync --dev`)
*   **Run Tests:** `make test` or `make test-dev`
*   **Lint Code:** `make lint` (runs `ruff check`)
*   **Fix Lint Issues:** `make fix` (runs `ruff check --fix` and `ruff format`)
*   **Type Check:** `make types` (runs `pyright`)
*   **Run All Checks:** `make check`
*   **Run Services:**
    *   To receive events: `uv run python retwitch_getter.py`
    *   To process events and handle commands: `uv run python retwitch_worker.py`
    *   To send messages to chat: `uv run python retwitch_sender.py`
*   **Authenticate with Twitch:** `uv run python twitch_cli.py` (to get the OAuth URL) and then `uv run python twitch_cli.py <code>` to save the token.

## Development Conventions
*   **Dependency Management:** Uses `uv` and `pyproject.toml`.
*   **Linting/Formatting:** Enforced by `ruff` with a specific configuration in `pyproject.toml`.
*   **Type Checking:** Performed using `pyright`.
*   **Testing:** Uses `pytest`. Tests likely utilize the `mock_redis` fixture defined in `conftest.py` to isolate tests from a real Redis instance.
*   **Code Style:** Generally follows Python best practices, with specific rules enforced by `ruff`. Single quotes are preferred for strings (via `ruff format` config).
