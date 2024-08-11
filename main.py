import logging
import time
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import pickle
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    cookie_path = Column(String, nullable=False)
    driver_session = Column(Boolean, default=False)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    post_url = Column(String, nullable=False)
    action_type = Column(String, nullable=False)  # 'comment' or 'reply'
    status = Column(String, nullable=False)  # 'pending', 'completed', 'failed'
    retries = Column(Integer, default=0)

engine = create_engine('sqlite:///users.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Store active driver sessions globally
active_drivers = {}

def add_user(username, password, cookie_path):
    try:
        user = User(username=username, password=password, cookie_path=cookie_path)
        session.add(user)
        session.commit()
        print(f"✅ User {username} added to the database.")
    except IntegrityError:
        session.rollback()
        print(f"⚠️ User {username} already exists in the database.")

def get_user(username):
    return session.query(User).filter_by(username=username).first()

def save_order(username, post_url, action_type):
    order = Order(username=username, post_url=post_url, action_type=action_type, status='pending')
    session.add(order)
    session.commit()
    return order.id

def update_order_status(order_id, status):
    order = session.query(Order).filter_by(id=order_id).first()
    order.status = status
    session.commit()

def increment_order_retries(order_id):
    order = session.query(Order).filter_by(id=order_id).first()
    order.retries += 1
    session.commit()

def login_instagram(driver, username, password):
    print(f"🔑 Logging in as {username}...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.send_keys(Keys.ENTER)
    time.sleep(5)
    print(f"✅ Logged in as {username}")

def save_cookies(driver, path):
    print(f"💾 Saving cookies to {path}...")
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print(f"✅ Cookies saved to {path}")

def load_cookies(driver, path):
    print(f"🍪 Loading cookies from {path}...")
    driver.get("https://www.instagram.com/")
    time.sleep(3)
    with open(path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(5)
    print(f"✅ Cookies loaded from {path}")

def login_or_load_cookies(driver, user):
    cookie_path = user.cookie_path
    if cookie_path and os.path.exists(cookie_path):
        load_cookies(driver, cookie_path)
    else:
        login_instagram(driver, user.username, user.password)
        save_cookies(driver, cookie_path)

def comment_on_post(driver, post_url, comment_text):
    for attempt in range(3):
        try:
            print(f"💬 Commenting on post: {post_url}...")
            driver.get(post_url)
            time.sleep(3)
            comment_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Add a comment…"]'))
            )
            comment_box.click()
            comment_box_active = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Add a comment…"]'))
            )
            comment_box_active.send_keys(comment_text)
            comment_box_active.send_keys(Keys.ENTER)
            time.sleep(3)
            print(f"✅ Commented on post: {post_url}")
            return True
        except Exception as e:
            print(f"❌ Error commenting on post: {post_url} - {e}")
            time.sleep(2)
    return False

def reply_to_story(driver, story_url, reply_text):
    for attempt in range(3):
        try:
            print(f"💬 Replying to story: {story_url}...")
            driver.get(story_url)
            time.sleep(3)
            reply_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Send Message…"]'))
            )
            reply_box.click()
            reply_box_active = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Send Message…"]'))
            )
            reply_box_active.send_keys(reply_text)
            reply_box_active.send_keys(Keys.ENTER)
            time.sleep(3)
            print(f"✅ Replied to story: {story_url}")
            return True
        except Exception as e:
            print(f"❌ Error replying to story: {story_url} - {e}")
            time.sleep(2)
    return False

def process_account(user, post_url=None, comment_text=None, story_url=None, reply_text=None):
    print(f"🚀 Starting process for {user.username}...")

    driver = active_drivers.get(user.username)

    if not driver:
        options = Options()
        options.headless = True  # Run in headless mode
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        login_or_load_cookies(driver, user)
        active_drivers[user.username] = driver
        user.driver_session = True
        session.commit()

    completed_comments = 0
    completed_replies = 0

    try:
        if comment_text:
            order_id = save_order(user.username, post_url, 'comment')
            for comment in comment_text:
                success = comment_on_post(driver, post_url, comment)
                if success:
                    completed_comments += 1
                    update_order_status(order_id, 'completed')
                else:
                    increment_order_retries(order_id)
                    update_order_status(order_id, 'failed')
                    break

        if reply_text:
            order_id = save_order(user.username, story_url, 'reply')
            for reply in reply_text:
                success = reply_to_story(driver, story_url, reply)
                if success:
                    completed_replies += 1
                    update_order_status(order_id, 'completed')
                else:
                    increment_order_retries(order_id)
                    update_order_status(order_id, 'failed')
                    break

    finally:
        print(f"🔒 Browser session remains open for {user.username}.")
        return completed_comments, completed_replies

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💬 Comment", callback_data='comment'),
            InlineKeyboardButton("📩 Reply to Story", callback_data='reply_to_story'),
            InlineKeyboardButton("👤 Add User", callback_data='add_user')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🤖 What do you want to do?', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'comment':
        await query.edit_message_text(text="📎 Send me the post URL.")
        context.user_data['action'] = 'comment_url'
    elif query.data == 'reply_to_story':
        await query.edit_message_text(text="📎 Send me the story URL.")
        context.user_data['action'] = 'reply_to_story_url'
    elif query.data == 'add_user':
        await query.edit_message_text(text="👤 Please send me the username.")
        context.user_data['action'] = 'add_user_username'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    if action == 'comment_url':
        context.user_data['post_url'] = update.message.text
        context.user_data['action'] = 'comment_texts'
        await update.message.reply_text("💬 Now, send me the comments separated by new lines.")
    elif action == 'comment_texts':
        post_url = context.user_data.get('post_url')
        comments = update.message.text.split('\n')
        comments = [comment.strip() for comment in comments if comment.strip()]
        users = session.query(User).all()
        total_comments = len(comments)
        for user in users:
            completed_comments, _ = process_account(user, post_url, comment_text=comments)
            await update.message.reply_text(
                f"👤 User {user.username} has completed {completed_comments}/{total_comments} comments."
            )
        await update.message.reply_text(f"🏁 All comment actions have been processed.")
    elif action == 'reply_to_story_url':
        context.user_data['story_url'] = update.message.text
        context.user_data['action'] = 'reply_texts'
        await update.message.reply_text("💬 Now, send me the replies separated by new lines.")
    elif action == 'reply_texts':
        story_url = context.user_data.get('story_url')
        replies = update.message.text.split('\n')
        replies = [reply.strip() for reply in replies if reply.strip()]
        users = session.query(User).all()
        total_replies = len(replies)
        for user in users:
            _, completed_replies = process_account(user, story_url=story_url, reply_text=replies)
            await update.message.reply_text(
                f"👤 User {user.username} has completed {completed_replies}/{total_replies} replies."
            )
        await update.message.reply_text(f"🏁 All reply actions have been processed.")
    elif action == 'add_user_username':
        context.user_data['username'] = update.message.text.strip()
        context.user_data['action'] = 'add_user_password'
        await update.message.reply_text("🔒 Please send me the password.")
    elif action == 'add_user_password':
        username = context.user_data.get('username')
        password = update.message.text.strip()
        cookie_folder = 'cookie'
        os.makedirs(cookie_folder, exist_ok=True)
        cookie_path = os.path.join(cookie_folder, f'cookie_{username}.pkl')
        add_user(username, password, cookie_path)

        options = Options()
        options.headless = True  # Run in headless mode
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        new_user = get_user(username)
        try:
            login_or_load_cookies(driver, new_user)
            active_drivers[username] = driver  # Store the active driver session
            new_user.driver_session = True
            session.commit()
            await update.message.reply_text(f"✅ User {username} added to the database and logged in successfully.")
        except Exception as e:
            await update.message.reply_text(f"❌ User {username} added but login failed: {e}")
        finally:
            # Keep the browser session open for further use
            context.user_data['driver'] = driver

def login_all_users():
    users = session.query(User).all()
    for user in users:
        options = Options()
        options.headless = True  # Run in headless mode
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        try:
            login_or_load_cookies(driver, user)
            active_drivers[user.username] = driver  # Store the active driver session
            user.driver_session = True
            session.commit()
            print(f"✅ Successfully logged in for user {user.username}")
        except Exception as e:
            print(f"❌ Failed to log in for user {user.username}: {e}")
            driver.quit()

def main():
    login_all_users()

    application = ApplicationBuilder().token('7325149894:AAGTxEjEVB5pFuV-kGN_4dEOCdX5GRfsVzo').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
