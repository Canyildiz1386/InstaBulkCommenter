import json
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging

# Disable all Selenium logging
logging.getLogger('selenium').setLevel(logging.ERROR)

def read_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f'Error reading data from file: {e}')
        return None

def read_post_url(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            url = file.readline().strip()
        return url
    except Exception as e:
        print(f'Error reading post URL from file: {e}')
        return None

def read_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            comments = [line.strip() for line in file if line.strip()]
        return comments
    except Exception as e:
        print(f'Error reading comments from file: {e}')
        return []

def filter_bmp_chars(text):
    # Filter out characters not in BMP (Basic Multilingual Plane)
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
        comment_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )

        comment_box.send_keys(comment_text)
        comment_box.send_keys(Keys.RETURN)

        return True
    except Exception as e:
        print(f'Failed to post comment: {e}')
        return False

def post_comments(data, post_url, comments):
    if data is None:
        print('No data to process')
        return

    num_users = len(data['accounts'])
    num_comments = len(comments)

    if num_users > num_comments:
        print('Not enough comments for the number of users')
        return

    for i, account in enumerate(data['accounts']):
        if i >= num_comments:
            print('Not enough comments for all users')
            break

        username = account['username']
        password = account['password']
        comment = filter_bmp_chars(comments[i])
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3") 
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        if login(driver, username, password):
            success = False
            while not success:
                if post_comment(driver, post_url, comment):
                    success = True
                    print(f'{username} posted comment: "{comment}" on {post_url}')
                else:
                    time.sleep(1)

        driver.quit()
    print("Finished")

if __name__ == "__main__":
    data_file = 'accounts.json'
    post_url_file = 'post_url.txt'
    comments_file = 'comments.txt'

    data = read_data(data_file)
    post_url = read_post_url(post_url_file)
    comments = read_comments(comments_file)

    post_comments(data, post_url, comments)
