import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import pickle
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    cookie_path = Column(String, nullable=False)
    driver_session = Column(Boolean, default=False)
    flag = Column(Boolean, default=False)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    post_url = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    retries = Column(Integer, default=0)

engine = create_engine('sqlite:///users.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

active_drivers = {}

def add_user(username, password, cookie_path):
    try:
        user = User(username=username, password=password, cookie_path=cookie_path)
        session.add(user)
        session.commit()
    except IntegrityError:
        session.rollback()

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
    driver.get("https://www.instagram.com/accounts/login/?next=https%3A%2F%2Fwww.instagram.com%2F&is_from_rle")
    time.sleep(3)
    try:
        driver.find_element(By.XPATH, "/html/body/div[5]/div[1]/div/div[2]/div/div/div/div/div[2]/div/button[1]").click()
    except Exception:
        pass
    username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/div/div/div[1]/div[2]/div/form/div/div[1]/div/label/input"))
        )
    password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div/div[1]/div[2]/div/form/div/div[2]/div/label/input"))
        )
    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.send_keys(Keys.ENTER)
    time.sleep(5)

def save_cookies(driver, path):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookies(driver, path):
    driver.get("https://www.instagram.com/")
    time.sleep(3)
    with open(path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(5)

def login_or_load_cookies(driver, user):
    cookie_path = user.cookie_path
    def is_logged_in(driver):
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
            )
            return True
        except Exception:
            return False
    if cookie_path and os.path.exists(cookie_path):
        load_cookies(driver, cookie_path)
        if not is_logged_in(driver):
            login_instagram(driver, user.username, user.password)
            save_cookies(driver, cookie_path)
    else:
        login_instagram(driver, user.username, user.password)
        save_cookies(driver, cookie_path)

def comment_exists(driver, post_url, comment_text):
    driver.get(post_url)
    time.sleep(3)
    comments = driver.find_elements(By.XPATH, "//div[@role='button']/span")
    for comment in comments:
        if comment_text in comment.text:
            return True
    return False

def comment_on_post(driver, post_url, comment_text):
    for attempt in range(3):
        try:
            driver.get(post_url)
            time.sleep(3 + random.uniform(1, 3))
            comment_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Add a comment…"]'))
            )
            comment_box.click()
            comment_box_active = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//textarea[@aria-label="Add a comment…"]'))
            )
            comment_box_active.send_keys(comment_text)
            comment_box_active.send_keys(Keys.ENTER)
            time.sleep(3 + random.uniform(1, 2))
            return True
        except Exception as e:
            time.sleep(2)
    return False

def process_account(user, post_url, comment_texts):
    driver = active_drivers.get(user.username)
    if not driver:
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(service=FirefoxService('geckodriver.exe'), options=options)
        login_or_load_cookies(driver, user)
        active_drivers[user.username] = driver
        user.driver_session = True
        session.commit()
    completed_comments = 0
    try:
        for comment_text in comment_texts:
            if comment_exists(driver, post_url, comment_text):
                continue
            success = comment_on_post(driver, post_url, comment_text)
            if success:
                completed_comments += 1
            else:
                break
        user.flag = True
        session.commit()
    finally:
        return completed_comments

def reset_user_flags():
    users = session.query(User).all()
    for user in users:
        user.flag = False
    session.commit()

last_user_index = -1

def distribute_comments_among_users(users, comments):
    global last_user_index
    assigned_comments = {}
    num_users = len(users)
    num_comments = len(comments)
    for i in range(num_comments):
        last_user_index = (last_user_index + 1) % num_users
        user = users[last_user_index]
        if user.username not in assigned_comments:
            assigned_comments[user.username] = []
        assigned_comments[user.username].append(comments[i])
    return assigned_comments

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💬 Comment", callback_data='comment'),
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
        users = session.query(User).filter_by(flag=False).all()
        if not users:
            reset_user_flags()
            users = session.query(User).filter_by(flag=False).all()
        assigned_comments = distribute_comments_among_users(users, comments)
        for username, user_comments in assigned_comments.items():
            user = session.query(User).filter_by(username=username).first()
            completed_comments = process_account(user, post_url=post_url, comment_texts=user_comments)
            if completed_comments > 0:
                await update.message.reply_text(
                    f"👤 User {username} has completed {completed_comments}/{len(user_comments)} comments."
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
        for user in users:
            completed_replies = process_account(user, story_url=story_url, reply_texts=replies)
            if completed_replies > 0:
                await update.message.reply_text(
                    f"👤 User {user.username} has completed {completed_replies}/{len(replies)} replies."
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
        options.add_argument('--headless')
        driver = webdriver.Firefox(service=FirefoxService('geckodriver.exe'), options=options)
        new_user = get_user(username)
        try:
            login_or_load_cookies(driver, new_user)
            active_drivers[username] = driver
            new_user.driver_session = True
            session.commit()
            await update.message.reply_text(f"✅ User {username} added to the database and logged in successfully.")
        except Exception as e:
            await update.message.reply_text(f"❌ User {username} added but login failed: {e}")

def login_all_users():
    users = session.query(User).all()
    for user in users:
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(service=FirefoxService('geckodriver.exe'), options=options)
        try:
            login_or_load_cookies(driver, user)
            active_drivers[user.username] = driver
            user.driver_session = True
            session.commit()
        except Exception as e:
            driver.quit()

def main():
    login_all_users()
    application = ApplicationBuilder().token('7447231078:AAFOZU4vSUdMvinjFqQekzglFkVyFEdv_ys').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()


