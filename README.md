# Instagram Comment Bot

Instagram Comment Bot is a Python project that automates the process of posting comments on Instagram posts using multiple accounts. This project utilizes Selenium for web automation and CustomTkinter for a graphical user interface to input comments and post URLs.

## Features

- Login to Instagram with multiple accounts
- Post comments on a specified Instagram post
- Graphical user interface for inputting post URL and comments
- Logs all activities for debugging and monitoring

## Prerequisites

- Python 3.7 or higher
- Google Chrome browser

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Canyildiz1386/InstaBulkCommenter.git
    cd instagram-comment-bot
    ```

2. Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Ensure you have `chromedriver` installed and it's in your PATH. You can download it from [here](https://sites.google.com/a/chromium.org/chromedriver/downloads).

## Usage

1. Prepare the `data.json` file with your Instagram accounts. The file should look like this:
    ```json
    {
        "accounts": [
            {
                "username": "your_username1",
                "password": "your_password1"
            },
            {
                "username": "your_username2",
                "password": "your_password2"
            }
        ]
    }
    ```

2. Run the script:
    ```bash
    python main.py
    ```

3. A GUI will prompt you to enter the Instagram post URL and comments for each account. After entering the information, the bot will log in to each account and post the comments.

## Project Structure

- `main.py`: Main script to run the bot.
- `data.json`: JSON file containing Instagram account credentials.
- `requirements.txt`: List of required Python packages.
- `instabot.log`: Log file containing bot activities.

## Logging

The bot logs all activities to `instabot.log` for debugging and monitoring purposes. You can check this file to see the status of the bot's operations.

## Dependencies

- `selenium`: For web automation.
- `webdriver_manager`: For managing web drivers.
- `customtkinter`: For the graphical user interface.
- `requests`, `beautifulsoup4`: For handling HTTP requests and parsing HTML (if needed).

Install these dependencies using the following command:
```bash
pip install selenium webdriver_manager customtkinter requests beautifulsoup4
