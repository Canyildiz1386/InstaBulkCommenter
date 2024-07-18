import json
import time
import random
import logging
import customtkinter as ctk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(filename='instabot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def read_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logging.info('Data loaded successfully from %s', file_path)
        return data
    except Exception as e:
        logging.error('Error reading data from file: %s', e)
        return None

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
        logging.info('Logged in successfully with username: %s', username)
        return True
    except Exception as e:
        logging.error('Failed to login with username %s: %s', username, e)
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
        
        logging.info('Comment posted: %s', comment_text)
        return True
    except Exception as e:
        logging.error('Failed to post comment: %s', e)
        return False

def post_comments(data, post_url):
    if data is None:
        logging.error('No data to process')
        return

    for account in data['accounts']:
        username = account['username']
        password = account['password']
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        
        if login(driver, username, password):
            comment = get_comment_from_user(username)
            if comment:
                success = False
                while not success:
                    if post_comment(driver, post_url, comment):
                        success = True
                    else:
                        time.sleep(300)  
                time.sleep(random.randint(60, 120)) 
        
        driver.quit()

def get_comment_from_user(username):
    root = ctk.CTk()
    root.withdraw()  # مخفی کردن پنجره اصلی

    class CommentDialog(ctk.CTkToplevel):
        def __init__(self, master, username):
            super().__init__(master)
            self.title("Enter Comment")
            self.geometry("400x200")
            self.username = username
            self.comment = None

            self.label = ctk.CTkLabel(self, text=f"Enter comment for {username}:")
            self.label.pack(pady=10)

            self.entry = ctk.CTkEntry(self, width=300)
            self.entry.pack(pady=10)

            self.button = ctk.CTkButton(self, text="Submit", command=self.submit)
            self.button.pack(pady=10)

        def submit(self):
            self.comment = self.entry.get()
            self.destroy()

    dialog = CommentDialog(root, username)
    root.wait_window(dialog)

    return dialog.comment

def get_post_url():
    root = ctk.CTk()
    root.withdraw()  # مخفی کردن پنجره اصلی

    class PostURLDialog(ctk.CTkToplevel):
        def __init__(self, master):
            super().__init__(master)
            self.title("Enter Post URL")
            self.geometry("400x200")
            self.post_url = None

            self.label = ctk.CTkLabel(self, text="Enter the Instagram post URL:")
            self.label.pack(pady=10)

            self.entry = ctk.CTkEntry(self, width=300)
            self.entry.pack(pady=10)

            self.button = ctk.CTkButton(self, text="Submit", command=self.submit)
            self.button.pack(pady=10)

        def submit(self):
            self.post_url = self.entry.get()
            self.destroy()

    dialog = PostURLDialog(root)
    root.wait_window(dialog)

    return dialog.post_url

if __name__ == "__main__":
    data_file = 'data.json'
    post_url = get_post_url()

    data = read_data(data_file)
    post_comments(data, post_url)
