
import json
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests

logging.basicConfig(filename='instabot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

SCRAPER_API_KEY = '91779949e54b37027b7c914dd06b8831'  # جایگزین کردن با API key خود

def read_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logging.info('Data loaded successfully from %s', file_path)
        return data
    except Exception as e:
        logging.error('Error reading data from file: %s', e)
        return None

def read_post_url(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            url = file.readline().strip()
        logging.info('Post URL loaded successfully from %s', file_path)
        return url
    except Exception as e:
        logging.error('Error reading post URL from file: %s', e)
        return None

def read_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            comments = [line.strip() for line in file if line.strip()]
        logging.info('Comments loaded successfully from %s', file_path)
        return comments
    except Exception as e:
        logging.error('Error reading comments from file: %s', e)
        return []

def login(driver, username, password):
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(3, 5))

        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")

        username_input.send_keys(username)
        time.sleep(random.uniform(1, 2))
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
        )
        logging.info('Logged in successfully with username: %s', username)
        return True
    except Exception as e:
        logging.error('Failed to login with username %s: %s', username, e)
        return False

def post_comment(driver, post_url, comment_text):
    try:
        driver.get(post_url)
        time.sleep(random.uniform(3, 5))

        comment_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )
        comment_box.click()
        comment_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
        )

        comment_box.send_keys(comment_text)
        time.sleep(random.uniform(1, 2))
        comment_box.send_keys(Keys.RETURN)
        
        logging.info('Comment posted: %s', comment_text)
        return True
    except Exception as e:
        logging.error('Failed to post comment: %s', e)
        return False

def get_proxied_url(url):
    return f'http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}'

def post_comments(data, post_url, comments):
    if data is None:
        logging.error('No data to process')
        return

    proxied_post_url = get_proxied_url(post_url)

    for account in data['accounts']:
        username = account['username']
        password = account['password']
        
        chrome_options = Options()
        print(get_proxied_url(""))
        chrome_options.add_argument('--proxy-server=%s' % get_proxied_url(""))

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        if login(driver, username, password):
            for comment in comments:
                success = False
                while not success:
                    if post_comment(driver, proxied_post_url, comment):
                        success = True
                        print(f'{username} posted comment: "{comment}" on {post_url}')
                    else:
                        time.sleep(300)
                time.sleep(random.uniform(60, 120))
        
        driver.quit()

if __name__ == "__main__":
    data_file = 'accounts.json'
    post_url_file = 'post_url.txt'
    comments_file = 'comments.txt'

    data = read_data(data_file)
    post_url = read_post_url(post_url_file)
    comments = read_comments(comments_file)

    post_comments(data, post_url, comments)
