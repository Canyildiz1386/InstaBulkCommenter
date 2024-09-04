# 📸 InstaBulkCommenter 🚀

Welcome to **InstaBulkCommenter**, a Python tool that helps you manage multiple Instagram accounts to automatically post comments on specified posts! This tool leverages **Instabot** and **Selenium** for seamless automated login and commenting. 

⚠️ **Please use this tool responsibly** and always adhere to Instagram's terms of service. This tool is designed to boost engagement, but it's important to follow the rules to avoid account restrictions. 

---

## ✨ Features

- 🔑 **Automated login**: No need to log in manually—InstaBulkCommenter handles that for you!
- 📝 **Bulk commenting**: Post multiple comments from different accounts on Instagram posts.
- 👥 **Manage multiple accounts**: Add, remove, and track multiple Instagram accounts easily.
- ⏱️ **Distribute comments**: Comments are distributed among users with intelligent logic to avoid spamming.
- 🔐 **Secure cookie storage**: Your login session is securely saved to prevent unnecessary login attempts.

---

## 🚀 Getting Started

### 🛠️ Prerequisites

Before running **InstaBulkCommenter**, make sure you have the following:

- **Python 3.8+**
- **Selenium WebDriver** for Firefox (i.e., `geckodriver`)
- **Instabot** (installed via `pip`)
- **Firefox** installed (since the tool is configured for Firefox automation)

### 📦 Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/InstaBulkCommenter.git
    ```

2. Navigate to the project directory:

    ```bash
    cd InstaBulkCommenter
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Download **geckodriver** for Selenium and ensure it is added to your system PATH. You can download it from here: [Geckodriver Download](https://github.com/mozilla/geckodriver/releases)

---

## ⚙️ How to Use

### 🔄 Step-by-Step Usage:

1. **Run the Application**:

    Once everything is set up, simply run the script:

    ```bash
    python main.py
    ```

2. **Start the Bot**:
    - The bot will prompt you with options like `💬 Comment` or `👤 Add User`. Use these to start interacting with Instagram.

3. **Adding Users**:
    - You can add multiple Instagram accounts. The bot will store credentials securely using cookies to automate the login process.
    - When prompted, send the username and password to log the bot into the accounts automatically.

4. **Commenting on Posts**:
    - Once accounts are added, send the Instagram post URL.
    - Then, send the comments you want to post, each separated by a new line.
    - The bot will distribute the comments across the different Instagram accounts and post them accordingly.

---

## 🚧 Advanced Usage

1. **Selenium Configuration**:
    - The bot uses **Selenium** with **Firefox** in headless mode. If you want to see the browser in action, you can modify the options by removing the `headless` argument in the `process_account` function.

2. **Handling Login Sessions**:
    - Login sessions are saved using cookies, so you don’t have to log in each time. The cookies are stored in the `cookie` folder.

3. **Reset User Flags**:
    - If accounts are flagged, you can reset user flags by calling the `reset_user_flags()` function in the script.

---

## 🛠 Troubleshooting

- **Login Issues**:
    If the bot is unable to log in, ensure that the Instagram login page has not changed, or update the XPath selectors accordingly.

- **Selenium Driver Errors**:
    Make sure **geckodriver** is installed and available in your system’s PATH. Also, ensure that **Firefox** is up-to-date.

- **Instagram Restrictions**:
    Be mindful of Instagram’s rate limits and terms of service. Too many login attempts or comments in a short period may result in temporary restrictions or bans.

---

## 📝 Disclaimer

**InstaBulkCommenter** is a tool for automating Instagram engagement tasks. Please use this tool responsibly and adhere to Instagram's policies. The developers are not responsible for any actions taken by Instagram as a result of misuse.

---

## 🏆 Credits

Created by **[Your Name]** ✨. Contributions and feedback are always welcome!

---

## 🔧 How to Build `.exe` (Windows)

Want to create an executable for this script? Follow these steps:

1. Install **PyInstaller**:

    ```bash
    pip install pyinstaller
    ```

2. Generate the `.exe` file:

    ```bash
    pyinstaller --onefile main.py
    ```

The resulting `.exe` file will be in the `dist/` folder!

---

Enjoy boosting your Instagram engagement responsibly! 🎉📈
