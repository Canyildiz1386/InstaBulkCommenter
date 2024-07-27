import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging
import threading
from sqlalchemy import create_engine, Column, Integer, String, Text, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from enum import Enum as PyEnum
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

Base = declarative_base()

class OrderStatus(PyEnum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    post_url = Column(Text, nullable=False)
    comment = Column(Text, nullable=False)
    account_username = Column(String, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

def read_data(file_path):
    print(f"Reading data from {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print("Data successfully read")
        return data
    except Exception as e:
        print(f'Error reading data from file: {e}')
        return None

def handle_suspicious_activity(driver):
    try:
        dismiss_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='button'][aria-label='Dismiss']"))
        )
        dismiss_button.click()
        print('Dismissed automated behavior warning.')
    except Exception as e:
        print(f'No dismiss button found: {e}')

def login(driver, username, password):
    print(f"Attempting to login with username: {username}")
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )

        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        handle_suspicious_activity(driver)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
        )

        print(f"Successfully logged in with username: {username}")
        return True
    except Exception as e:
        print(f'Failed to login with username {username}: {e}')
        return False

def post_comment(driver, post_url, comment_text, retries=3):
    for attempt in range(retries):
        print(f"Attempt {attempt + 1} to post comment on {post_url}")
        try:
            driver.get(post_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            comment_box = driver.find_element(By.CSS_SELECTOR, "textarea")
            driver.execute_script("arguments[0].scrollIntoView();", comment_box)
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea"))
            )

            try:
                close_button = driver.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label='Close']")
                close_button.click()
            except NoSuchElementException:
                pass

            comment_box.click()
            comment_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )

            comment_box.send_keys(comment_text)
            comment_box.send_keys(Keys.RETURN)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            print("Comment posted successfully")
            return True
        except ElementClickInterceptedException as e:
            print(f'Attempt {attempt + 1} failed to post comment: {e}')
            if attempt == retries - 1:
                return False
            time.sleep(5)
        except (NoSuchElementException, TimeoutException) as e:
            print(f'Attempt {attempt + 1} failed to post comment: {e}')
            if attempt == retries - 1:
                return False
            time.sleep(5)
        except Exception as e:
            print(f'An unexpected error occurred: {e}')
            return False

def login_accounts(data):
    print("Logging in all accounts")
    drivers = {}
    for account in data['accounts']:
        username = account['username']
        password = account['password']

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(service=Service('chromedriver.exe'), options=chrome_options)
        if login(driver, username, password):
            drivers[username] = driver
            print(f'{username} logged in successfully')
        else:
            driver.quit()
    return drivers

def process_order(driver, order_id, session_factory):
    session = session_factory()
    order = session.query(Order).get(order_id)
    post_url = order.post_url
    comment = order.comment
    account_username = order.account_username

    if driver:
        success = post_comment(driver, post_url, comment)
        if success:
            order.status = OrderStatus.COMPLETED
            print(f'Order {order.id} completed by {account_username}')
        else:
            order.status = OrderStatus.FAILED
            print(f'Failed to post comment for order {order.id} by {account_username}')
    else:
        order.status = OrderStatus.FAILED
        print(f'No active session for {account_username}')

    session.commit()
    session.close()

def process_orders_concurrently(drivers, session_factory):
    while True:
        session = session_factory()
        orders = session.query(Order).filter(Order.status == OrderStatus.PENDING).all()
        session.close()
        threads = []
        if orders:
            print("Processing new orders")
            for order in orders:
                driver = drivers.get(order.account_username)
                if driver:
                    thread = threading.Thread(target=process_order, args=(driver, order.id, session_factory))
                    threads.append(thread)
                    thread.start()
                else:
                    print(f"No driver found for {order.account_username}, skipping order {order.id}")

            for thread in threads:
                thread.join()

        time.sleep(10)

class AccountsFileHandler(FileSystemEventHandler):
    def __init__(self, drivers, data_file, session_factory):
        self.drivers = drivers
        self.data_file = data_file
        self.session_factory = session_factory

    def on_modified(self, event):
        if event.src_path.endswith(self.data_file):
            print("accounts.json has been modified.")
            new_data = read_data(self.data_file)
            if new_data:
                self.update_accounts(new_data)

    def update_accounts(self, new_data):
        for account in new_data['accounts']:
            username = account['username']
            if username not in self.drivers:
                password = account['password']
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')

                driver = webdriver.Chrome(service=Service('chromedriver.exe'), options=chrome_options)
                if login(driver, username, password):
                    self.drivers[username] = driver
                    print(f'{username} logged in successfully')
                else:
                    driver.quit()

if __name__ == "__main__":
    data_file = 'accounts.json'
    db_url = 'sqlite:///orders.db'

    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)

    start = time.time()
    data = read_data(data_file)

    if data:
        drivers = login_accounts(data)
        if drivers:
            print("All accounts logged in. Checking for new orders...")

            event_handler = AccountsFileHandler(drivers, data_file, SessionFactory)
            observer = Observer()
            observer.schedule(event_handler, path='.', recursive=False)
            observer.start()

            try:
                process_orders_concurrently(drivers, SessionFactory)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
        else:
            print("Failed to log in any accounts.")
    else:
        print("No account data found.")

    finish = time.time() - start
    print(f'Finished in {round(finish, 2)} seconds')
