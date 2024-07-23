import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from enum import Enum as PyEnum

# Disable all Selenium logging
logging.getLogger('selenium').setLevel(logging.ERROR)

Base = declarative_base()

class OrderStatus(PyEnum):
    PENDING = 'pending'
    COMPLETED = 'completed'

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    post_url = Column(Text, nullable=False)
    comment = Column(Text, nullable=False)
    account_username = Column(String, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

def read_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f'Error reading data from file: {e}')
        return None

def filter_bmp_chars(text):
    return re.sub(r'[^\u0000-\uFFFF]', '', text)

def login(driver, username, password):
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(2)

        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")

        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
        )
        return True
    except Exception as e:
        print(f'Failed to login with username {username}: {e}')
        return False

def post_comment(driver, post_url, comment_text):
    try:
        driver.get(post_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )

        comment_box = driver.find_element(By.CSS_SELECTOR, "textarea")
        comment_box.click()
        comment_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )

        comment_box.send_keys(comment_text)
        comment_box.send_keys(Keys.RETURN)

        return True
    except Exception as e:
        print(f'Failed to post comment: {e}')
        return False

def login_accounts(data):
    drivers = {}
    for account in data['accounts']:
        username = account['username']
        password = account['password']
        
        firefox_options = Options()
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--log-level=3")
        firefox_options.add_argument("--headless")

        driver = webdriver.Firefox(service=Service('geckodriver.exe'), options=firefox_options)
        if login(driver, username, password):
            drivers[username] = driver
            print(f'{username} logged in successfully')
        else:
            driver.quit()
    return drivers

def store_comments_in_db(session, post_url, comments, account_usernames):
    for comment, account_username in zip(comments, account_usernames):
        new_order = Order(post_url=post_url, comment=comment, account_username=account_username)
        session.add(new_order)
    session.commit()

def process_orders(drivers, session):
    while True:
        orders = session.query(Order).filter(Order.status == OrderStatus.PENDING).all()
        if orders:
            for order in orders:
                post_url = order.post_url
                comment = order.comment
                account_username = order.account_username

                driver = drivers.get(account_username)
                if driver:
                    success = post_comment(driver, post_url, comment)
                    if success:
                        order.status = OrderStatus.COMPLETED
                        session.commit()
                        print(f'Order {order.id} completed by {account_username}')
                else:
                    print(f'No active session for {account_username}')

        time.sleep(10)

if __name__ == "__main__":
    data_file = 'accounts.json'
    db_url = 'sqlite:///orders.db'
    
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Comments to be posted
    comments = [
        "شیک 💜💙💚",
        "عاطی نمونه کارات حرف نداره",
        "چه قشنگ 😘😘😘",
        "بی  نظیری 😍",
        "شیک 💜💙💚",
        "محشره 🔥🔥🔥🔥",
        "شمارتونو میزارید لطفا 🙏",
        "چه جذابه",
        "چه خوشگل شده",
        "عالیه هنرمند جان🙏",
        "ولو",
        "عالیه💚💚💚💚",
        "حرفه ای🔥🔥🔥",
        "حرفه ای🔥🔥🔥",
        "لاکش چه رنگیه ؟؟",
        "چه زیباست💚💚💚💚",
        "اوووووف 🤩🤩🤩",
        "اوووووف 🤩🤩🤩"
    ]

    # Post URL
    post_url = "https://www.instagram.com/p/C9SP5mNtdfq/"

    start = time.time()
    data = read_data(data_file)

    if data:
        drivers = login_accounts(data)
        if drivers:
            print("All accounts logged in. Storing comments in the database...")
            account_usernames = [account['username'] for account in data['accounts']]
            store_comments_in_db(session, post_url, comments, account_usernames)
            print("Comments stored. Checking for new orders...")
            process_orders(drivers, session)
        else:
            print("Failed to log in any accounts.")
    else:
        print("No account data found.")

    finish = time.time() - start
    print(f'Finished in {round(finish, 2)} seconds')
