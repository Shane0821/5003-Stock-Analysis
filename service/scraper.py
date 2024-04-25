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
    def __init__(self, ticker_symbol, on_data):
        self.ticker_symbol = ticker_symbol
        self.options = Options()
        self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.is_running = False
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                        options=self.options)
        self.driver.set_window_size(1920, 1080)
        self.on_data = on_data # callback on data

    def __del__(self):
        self.stop()
        self.driver.quit()

    def scrape(self):
        while (self.is_running):
            summary_data = self.get_summary_data()
            regular_market_data = self.get_regular_market_data()

            raw_data = regular_market_data | summary_data
            
            self.on_data(self.ticker_symbol, raw_data)
            
            time.sleep(5)

    def start(self):
        self.driver.get(f'https://finance.yahoo.com/quote/{self.ticker_symbol}')
        self.is_running = True
        self.scraper = threading.Thread(target=self.scrape)
        self.scraper.start()
    
    def stop(self):
        self.is_running = False
        if self.scraper:
            self.scraper.join()

    def get_regular_market_data(self):
        try:
            regular_market_price = self.driver.find_element(
                By.CSS_SELECTOR,  f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketPrice"]').text
            regular_market_change = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketChange"]').text
            regular_market_change_percent = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketChangePercent"]').text
            
            data = {}
            data['regular_market_price'] = regular_market_price
            data['regular_market_change'] = regular_market_change
            data['regular_market_change_percent'] = regular_market_change_percent
            return data
        except:
            return {}

    def get_summary_data(self):
        # TODO: move data processing to spark streaming
        try:
            regular_market_previous_close = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketPreviousClose"]').text
            regular_market_open = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketOpen"]').text
            bid = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[3]/span[2]').text
            ask = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[4]/span[2]').text
            regular_market_volume = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="regularMarketVolume"]').text
            average_volume = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="averageVolume"]').text
            market_cap = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="marketCap"]').text
            beta = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[10]/span[2]').text
            pe_ratio = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[11]/span[2]/fin-streamer').text
            eps = self.driver.find_element(
                By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[2]/ul/li[12]/span[2]/fin-streamer').text
            one_year_target_est = self.driver.find_element(
                By.CSS_SELECTOR, f'[data-symbol="{self.ticker_symbol}"][data-field="targetMeanPrice"]').text

            data = {}
            data['regular_market_previous_close'] = regular_market_previous_close
            data['regular_market_open'] = regular_market_open
            data['bid'] = bid
            data['ask'] = ask
            data['regular_market_volume'] = regular_market_volume
            data['average_volume'] = average_volume
            data['market_cap'] = market_cap
            data['beta'] = beta
            data['pe_ratio'] = pe_ratio
            data['eps'] = eps
            data['1y_target_est'] = one_year_target_est

            return data
        except:
            return {}
        

# scraper = Scraper('AAPL', on_data=lambda x: print(x))

# scraper.start()
# time.sleep(20)
# scraper.stop()

# print("stopped")
# time.sleep(10)

# scraper.start()
# time.sleep(20)
# scraper.stop()