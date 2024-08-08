import logging
import time
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, Column, String, Integer
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

engine = create_engine('sqlite:///users.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def add_user(username, password, cookie_path):
    try:
        user = User(username=username, password=password, cookie_path=cookie_path)
        session.add(user)
        session.commit()
        print(f"✅ User {username} added to the database.")
    except IntegrityError:
        session.rollback()
        print(f"⚠️ User {username} already exists in the database.")

add_user("Canyildiz1386", "Rahyab1357", "cookies_Canyildiz1386.pkl")

def get_user(username):
    return session.query(User).filter_by(username=username).first()

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

def like_post(driver, post_url):
    print(f"❤️ Liking post: {post_url}...")
    driver.get(post_url)
    time.sleep(3)
    like_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//span[@aria-label="Like"]'))
    )
    like_button.click()
    time.sleep(2)
    print(f"✅ Liked post: {post_url}")

def process_account(user, post_url, comment_text=None, likes=0):
    print(f"🚀 Starting process for {user.username}...")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service)
    try:
        login_or_load_cookies(driver, user)
        if comment_text:
            for comment in comment_text:
                comment_on_post(driver, post_url, comment)
        for _ in range(likes):
            like_post(driver, post_url)
    finally:
        driver.quit()
        print(f"🔒 Closed browser for {user.username}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Comment", callback_data='comment'),
            InlineKeyboardButton("Like", callback_data='like'),
            InlineKeyboardButton("Add User", callback_data='add_user')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('What do you want to do?', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'comment':
        await query.edit_message_text(text="Send me the post URL.")
        context.user_data['action'] = 'comment_url'
    elif query.data == 'like':
        await query.edit_message_text(text="Send me the post URL.")
        context.user_data['action'] = 'like_url'
    elif query.data == 'add_user':
        await query.edit_message_text(text="Send me the username, password, and cookie path separated by commas.")
        context.user_data['action'] = 'add_user'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    if action == 'comment_url':
        context.user_data['post_url'] = update.message.text
        context.user_data['action'] = 'comment_texts'
        await update.message.reply_text("Now, send me the comments separated by new lines.")
    elif action == 'comment_texts':
        post_url = context.user_data.get('post_url')
        comments = update.message.text.split('\n')
        comments = [comment.strip() for comment in comments if comment.strip()]
        users = session.query(User).all()
        threads = []
        for user in users:
            thread = threading.Thread(target=process_account, args=(user, post_url, comments))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        await update.message.reply_text(f"🏁 All comments have been posted.")
    elif action == 'like_url':
        context.user_data['post_url'] = update.message.text
        context.user_data['action'] = 'like_count'
        await update.message.reply_text("How many likes do you want to give?")
    elif action == 'like_count':
        try:
            post_url = context.user_data.get('post_url')
            likes = int(update.message.text)
            users = session.query(User).all()
            threads = []
            for user in users:
                thread = threading.Thread(target=process_account, args=(user, post_url, None, likes))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            await update.message.reply_text(f"🏁 All likes have been completed.")
        except Exception as e:
            await update.message.reply_text(f"❌ An error occurred: {e}")
    elif action == 'add_user':
        try:
            username, password, cookie_path = update.message.text.split(',')
            add_user(username.strip(), password.strip(), cookie_path.strip())
            await update.message.reply_text(f"✅ User {username.strip()} added to the database.")
        except Exception as e:
            await update.message.reply_text(f"❌ An error occurred: {e}")

def main():
    application = ApplicationBuilder().token('7325149894:AAGTxEjEVB5pFuV-kGN_4dEOCdX5GRfsVzo').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
