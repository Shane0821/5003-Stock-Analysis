from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException
import time


# build the URL of the target page
ticker_symbol = 'ASML'
url = f'https://finance.yahoo.com/quote/{ticker_symbol}'

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# initialize a web driver instance to control a Chrome window
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                          options=options)
driver.set_window_size(1920, 1080)
driver.get(url)

def get_pre_market_data():
    try:
        pre_market_price = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="preMarketPrice"]').text.replace(',', '')
        pre_market_change = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="preMarketChange"]').text
        pre_market_change_percent = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="preMarketChangePercent"]').text\
                .replace('(', '').replace(')', '')
        
        data = {}
        data['pre_market_price'] = float(pre_market_price)
        data['pre_market_change'] = float(pre_market_change)
        data['pre_market_change_percent'] = float(pre_market_change_percent[:-1])
        return data
    except:
        return {}

def get_post_market_data():
    try:
        post_market_price = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="postMarketPrice"]').text.replace(',', '')
        post_market_change = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="postMarketChange"]').text
        post_market_change_percent = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="postMarketChangePercent"]').text\
                .replace('(', '').replace(')', '')
        
        data = {}
        data['post_market_price'] = float(post_market_price)
        data['post_market_change'] = float(post_market_change)
        data['post_market_change_percent'] = float(post_market_change_percent[:-1])
        return data
    except:
        return {}

def get_regular_market_data():
    try:
        regular_market_price = driver.find_element(
            By.CSS_SELECTOR,  f'[data-symbol="{ticker_symbol}"][data-field="regularMarketPrice"]').text.replace(',', '')
        regular_market_change = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="regularMarketChange"]').text
        regular_market_change_percent = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="regularMarketChangePercent"]')\
                .text.replace('(', '').replace(')', '')
        
        data = {}
        data['regular_market_price'] = float(regular_market_price)
        data['regular_market_change'] = float(regular_market_change)
        data['regular_market_change_percent'] = float(regular_market_change_percent[:-1])
        return data
    except:
        return {}

def get_summary_data():
    try:
        regular_market_previous_close = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="regularMarketPreviousClose"]').text.replace(',', '')
        regular_market_open = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="regularMarketOpen"]').text.replace(',', '')
        bid = driver.find_element(
            By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[3]/span[2]').text.replace(',', '')
        ask = driver.find_element(
            By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[4]/span[2]').text.replace(',', '')
        regular_market_volume = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="regularMarketVolume"]').text.replace(',', '')
        average_volume = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="averageVolume"]').text.replace(',', '')
        market_cap = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="marketCap"]').text
        beta = driver.find_element(
            By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[10]/span[2]').text
        pe_ratio = driver.find_element(
            By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[11]/span[2]/fin-streamer').text
        eps = driver.find_element(
            By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[12]/span[2]/fin-streamer').text
        one_year_target_est = driver.find_element(
            By.CSS_SELECTOR, f'[data-symbol="{ticker_symbol}"][data-field="targetMeanPrice"]').text.replace(',', '')

        data = {}
        data['regular_market_previous_close'] = float(regular_market_previous_close) if regular_market_previous_close != '--' else 0
        data['regular_market_open'] = float(regular_market_open) if regular_market_open != '--' else 0
        data['bid_price'] = bid.split(' x ')[0] if bid != '--' else 0
        data['bid_size'] = bid.split(' x ')[1] if bid != '--' else 0
        data['ask_price'] = ask.split(' x ')[0] if ask != '--' else 0
        data['ask_size'] = ask.split(' x ')[1] if ask != '--' else 0
        data['regular_market_volume'] = int(regular_market_volume) if regular_market_volume != '--' else 0
        data['average_volume'] = int(average_volume) if average_volume != '--' else 0
        data['market_cap'] = float(market_cap[:-1])
        data['market_cap_scale'] = 0 if market_cap[-1] == '' else 1 if market_cap[-1] == 'M' else 2 if market_cap[-1] == 'B' else 3
        data['beta'] = float(beta) if beta != '--' else 0
        data['pe_ratio'] = float(pe_ratio) if pe_ratio != '--' else 0
        data['eps'] = float(eps) if eps != '--' else 0
        data['1y_target_est'] = float(one_year_target_est) if one_year_target_est != '--' else 0

        return data
    except:
        return {}

while (True):
    regular_market_data = get_regular_market_data()
    pre_market_data = get_pre_market_data()
    post_market_data = get_post_market_data()
    summary_data = get_summary_data()

    raw_data = regular_market_data | pre_market_data | post_market_data | summary_data
    
    print(raw_data)
    
    time.sleep(10)


# close the browser and free up the resources
driver.quit()