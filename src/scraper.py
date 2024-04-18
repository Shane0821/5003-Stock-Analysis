from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException
import time
import threading

class Scraper:
    def __init__(self, ticker_symbol):
        self.ticker_symbol = ticker_symbol
        self.options = Options()
        self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.is_running = False
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                        options=self.options)
        self.driver.set_window_size(1920, 1080)

    def __del__(self):
        self.stop()
        self.driver.quit()

    def scrape(self):
        while (self.is_running):
            regular_market_data = self.get_regular_market_data()
            pre_market_data = self.get_pre_market_data()
            post_market_data = self.get_post_market_data()
            summary_data = self.get_summary_data()

            raw_data = regular_market_data | pre_market_data | post_market_data | summary_data
            
            print(raw_data)
            
            time.sleep(5)

    def start(self):
        self.driver.get(f'https://finance.yahoo.com/quote/{self.ticker_symbol}')
        self.is_running = True
        self.scraper = threading.Thread(target=self.scrape)
        self.scraper.start()
    
    def stop(self):
        self.is_running = False
        self.scraper.join()

    def get_pre_market_data(self):
        try:
            pre_market_price = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="preMarketPrice"]').text.replace(',', '')
            pre_market_change = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="preMarketChange"]').text
            pre_market_change_percent = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="preMarketChangePercent"]').text\
                    .replace('(', '').replace(')', '')
            
            data = {}
            data['pre_market_price'] = float(pre_market_price)
            data['pre_market_change'] = float(pre_market_change)
            data['pre_market_change_percent'] = float(pre_market_change_percent[:-1])
            return data
        except:
            return {}

    def get_post_market_data(self):
        try:
            post_market_price = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="postMarketPrice"]').text.replace(',', '')
            post_market_change = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="postMarketChange"]').text
            post_market_change_percent = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="postMarketChangePercent"]').text\
                    .replace('(', '').replace(')', '')
            
            data = {}
            data['post_market_price'] = float(post_market_price)
            data['post_market_change'] = float(post_market_change)
            data['post_market_change_percent'] = float(post_market_change_percent[:-1])
            return data
        except:
            return {}

    def get_regular_market_data(self):
        try:
            regular_market_price = self.driver.find_element(
                By.CSS_SELECTOR,  f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketPrice"]').text.replace(',', '')
            regular_market_change = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketChange"]').text
            regular_market_change_percent = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketChangePercent"]')\
                    .text.replace('(', '').replace(')', '')
            
            data = {}
            data['regular_market_price'] = float(regular_market_price)
            data['regular_market_change'] = float(regular_market_change)
            data['regular_market_change_percent'] = float(regular_market_change_percent[:-1])
            return data
        except:
            return {}

    def get_summary_data(self):
        # TODO: move data processing to spark streaming
        try:
            regular_market_previous_close = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketPreviousClose"]').text.replace(',', '')
            regular_market_open = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketOpen"]').text.replace(',', '')
            bid = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[3]/span[2]').text.replace(',', '')
            ask = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[4]/span[2]').text.replace(',', '')
            regular_market_volume = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketVolume"]').text.replace(',', '')
            average_volume = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="averageVolume"]').text.replace(',', '')
            market_cap = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="marketCap"]').text
            beta = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[10]/span[2]').text
            pe_ratio = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[11]/span[2]/fin-streamer').text
            eps = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[12]/span[2]/fin-streamer').text
            one_year_target_est = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="targetMeanPrice"]').text.replace(',', '')

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
        

# scraper = Scraper('AAPL')

# scraper.start()
# time.sleep(20)
# scraper.stop()

# print("stopped")
# time.sleep(10)

# scraper.start()
# time.sleep(20)
# scraper.stop()