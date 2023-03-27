from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import json
import os
from tkinter import filedialog
from tkinter import messagebox
from tkinter import *
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
from functools import partial
import undetected_chromedriver as uc


def is_logged_in(driver):
    driver.get(
        'https://www.redbubble.com/portfolio/manage_works?ref=account-nav-dropdown')
    time.sleep(0.5)
    return driver.current_url != 'https://www.redbubble.com/auth/login'


def get_template_link(driver):
    # Manual selection
    # return 'https://www.redbubble.com/portfolio/images/12345678-artwork-title/duplicate'

    # Automatic selection
    driver.get(
        'https://www.redbubble.com/portfolio/manage_works?ref=account-nav-dropdown')
    return BeautifulSoup(driver.page_source, 'html.parser').find('a', class_='works_work-menu-option works_work-menu-option__duplicate')['href']


def create_driver():
    chromedriver_autoinstaller.install()
    options = uc.ChromeOptions()
    options.add_argument('--user-data-dir=' + os.path.join(
        os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default'))
    return uc.Chrome()


def is_image(file):
    return file[-3:] == 'png' or file[-3:] == 'jpg'


class Design:
    def __init__(self, dir, file):
        self.location = f'{dir}/{file}'
        self.title = file[:-4]

        tags = None
        if os.path.exists(dir + '/data.json'):
            with open(dir + '/data.json', 'r') as f:
                data = json.load(f)
            tags = [', '.join(data[self.title]['tags'])]

        if '(' in self.title:
            self.title = self.title.split('(')[0].title().replace('-', ' ')
        else:
            self.title = self.title.title().replace('-', ' ')

        self.tags = ', '.join(self.title.split()) if tags is None else tags
        self.desc = f'{self.title}: {", ".join(self.tags)}'

    def __repr__(self):
        return f'RB Design: {self.title}'


class Bot:
    def __init__(self):
        self.designs = []

    def add_designs(self, dir):
        self.designs += [Design(dir, file)
                         for file in os.listdir(dir) if is_image(file)]

    def upload_designs(self):
        driver = create_driver()
        if not is_logged_in(driver):
            print('You must login into Redbubble. If you are using the same Chrome Profile, you only need to do this once\nOnce you login, the bot will automatically continue')
            wait = WebDriverWait(driver, 300)
            # This should be the landing page after logging in
            wait.until(lambda driver: driver.current_url == "https://www.redbubble.com/explore/for-you/#" or driver.current_url ==
                       'https://www.redbubble.com/portfolio/manage_works?ref=account-nav-dropdown')

        template_link = get_template_link(driver)
        start = time.time()
        for design in self.designs:
            driver.get(template_link)

            wait = WebDriverWait(driver, 600)
            element = wait.until(lambda x: x.find_element(
                "css selector", "#select-image-single")).send_keys(design.location)

            time.sleep(6)
            element = driver.find_element("css selector", '#work_title_en')
            element.clear()
            element.send_keys(design.title)

            time.sleep(7)
            element = driver.find_element("css selector", '#work_tag_field_en')
            element.clear()
            element.send_keys(design.tags)

            time.sleep(8)
            element = driver.find_element(
                "css selector", '#work_description_en')
            element.clear()
            element.send_keys(design.desc)

            time.sleep(9)
            driver.find_element("css selector", '#rightsDeclaration').click()

            time.sleep(10)
            element = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit-work")))
            element.click()

            wait = WebDriverWait(driver, 60)
            wait.until(
                lambda driver: 'https://www.redbubble.com/studio/promote' in driver.current_url)
        print(
            f'Uploaded {len(self.designs)} Design(s) in {round((time.time()-start) / 60, 2)} Minutes')
        driver.quit()


def run_gui():
    bot = Bot()
    current_row = ['']
    root = Tk()

    def open_dir(current_row):
        root.filename = filedialog.askdirectory(
            title='Select A Folder With Your Designs')
        if root.filename != '':
            dir_entry = Entry(root, width=50)
            dir_entry.insert(0, root.filename)
            dir_entry.grid(row=len(current_row), column=0)
            found_desings_label = Label(root, text='Found ' + str(
                len([file for file in os.listdir(root.filename) if is_image(file)])) + ' Designs')
            found_desings_label.grid(row=len(current_row), column=1)
            upload_button.grid(row=len(current_row)+1, column=0, pady=(15, 15))
            current_row.append('')
            bot.add_designs(root.filename)

    def upload():
        if len(bot.designs) != 0:
            bot.upload_designs()
        else:
            messagebox.showwarning(
                'Empty Fields', 'Please select at least one folder with valid designs')

    open_dir_current = partial(open_dir, current_row)
    dir_button = Button(root, text='ADD DESIGNS', command=open_dir_current)
    upload_button = Button(root, text='UPLOAD', command=upload)
    dir_button.grid(row=0, column=0)

    root.mainloop()


if __name__ == '__main__':
    run_gui()
