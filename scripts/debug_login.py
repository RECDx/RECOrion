import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

opt = Options()
opt.add_argument('--headless')
opt.add_argument('--window-size=1600,1000')
driver = webdriver.Chrome(options=opt)
try:
    driver.get('http://localhost:5173/')
    time.sleep(1)
    driver.find_element(By.XPATH, "//button[contains(text(), 'Giriş Yap')]").click()
    time.sleep(1)
    driver.find_element(By.XPATH, "//button[contains(text(), 'RECDx Süper Admin Bilgilerini Doldur')]").click()
    time.sleep(1)
    email_val = driver.find_element(By.XPATH, "//input[@type='email']").get_attribute('value')
    pass_val = driver.find_element(By.XPATH, "//input[@type='password']").get_attribute('value')
    print('FILLED EMAIL:', email_val, 'PASS LENGTH:', len(pass_val))
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(3)
    os.makedirs('screenshots', exist_ok=True)
    driver.save_screenshot('screenshots/debug_after_submit.png')
    print('SAVED screenshots/debug_after_submit.png')
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print('BODY TEXT SAMPLE:', body_text[:400].replace('\n', ' '))
    print('--- BROWSER CONSOLE LOGS ---')
    for log in driver.get_log('browser'):
        print('BROWSER LOG:', log)
finally:
    driver.quit()
