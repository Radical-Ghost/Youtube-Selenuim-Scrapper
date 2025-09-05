import re
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import psutil
import tracemalloc
import pandas as pd

# Global variables for performance tracking
data_record_table = pd.DataFrame(columns=['Sr.no.', 'Total Time', 'Process Time', 'Data Used', 'Memory Used'])
j = 0

class YoutubeSeleniumSpider(scrapy.Spider):
    name = 'youtube_selenium'
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.video_data = []
        
    def setup_driver(self):
        """Setup Chrome driver with optimal settings"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
        except:
            # Fallback to manual path
            service = Service("chromedriver.exe")
            self.driver = webdriver.Chrome(service=service, options=options)
        
        return self.driver
    
    def start_requests(self):
        url = "https://www.youtube.com/@knowledgebase7115/videos"
        list_link = []
        count = 0
        final_count = 100  # Reduced for better performance
        
        # Setup driver
        driver = self.setup_driver()
        
        try:
            driver.maximize_window()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            scroll_pause_time = 2
            
            self.logger.info(f"Starting to collect up to {final_count} video links...")
            
            while count < final_count:
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(scroll_pause_time)
                
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                
                if new_height == last_height:
                    self.logger.info("Reached end of page")
                    break
                last_height = new_height
                
                html = driver.page_source
                soup = BeautifulSoup(html, features='lxml')
                
                for video in soup.find_all('div', attrs={'id': "details"}):
                    try:
                        link_element = video.find('a', attrs={'id': "video-title-link"})
                        if link_element:
                            link = "https://www.youtube.com" + link_element.get('href')
                            if link not in list_link:
                                list_link.append(link)
                                self.logger.info(f"Found video {len(list_link)}: {link}")
                                count += 1
                                if count >= final_count:
                                    break
                    except Exception as e:
                        self.logger.error(f"Error extracting link: {e}")
                        continue
            
            self.logger.info(f"Successfully collected {len(list_link)} video links")
            
        except Exception as e:
            self.logger.error(f"Error during link collection: {e}")
        finally:
            driver.quit()
        
        # Generate requests for each video
        for video_link in list_link:
            yield scrapy.Request(url=video_link, callback=self.parse, meta={'video_url': video_link})

    def parse(self, response):
        global j, data_record_table
        
        video_url = response.meta.get('video_url', response.url)
        
        # Setup new driver for this video
        driver = self.setup_driver()
        
        title_text = "Error"
        num_likes = "0"
        num_views = "0"
        date_vid = "Error"
        
        try:
            # Performance monitoring start
            tracemalloc.start()
            mu_start_1, mu_stop_1 = tracemalloc.get_traced_memory()
            start_time = time.process_time()
            start_time_total = time.time()
            old_data = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
            
            driver.get(video_url)
            self.logger.info(f"Loading video: {video_url}")
            
            # Wait for page to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.ytd-watch-metadata'))
            )
            
            # Try to expand description
            try:
                expand_button = driver.find_element(By.ID, 'expand')
                if expand_button:
                    expand_button.click()
                    time.sleep(2)
            except:
                pass
            
            html = driver.page_source
            soup = BeautifulSoup(html, features='lxml')
            
            # Extract data
            try:
                title_element = soup.find('yt-formatted-string', attrs={'class': "style-scope ytd-watch-metadata"})
                title_text = title_element.text if title_element else "Title not found"
                
                # Extract likes
                try:
                    likes_element = soup.find('like-button-view-model', attrs={'class': "YtLikeButtonViewModelHost"})
                    if likes_element:
                        button = likes_element.find('button')
                        if button and button.get('aria-label'):
                            num_likes = ''.join(re.findall(r'\d+', button.get('aria-label')))
                        else:
                            num_likes = "0"
                    else:
                        num_likes = "0"
                except:
                    num_likes = "0"
                
                # Extract views and date
                try:
                    info_element = soup.find('yt-formatted-string', attrs={'id': "info"})
                    if info_element:
                        vid_info = info_element.text
                        if ' views ' in vid_info:
                            num_views, date_vid = vid_info.split(' views ', 1)
                            num_views = ''.join(re.findall(r'\d+', num_views))
                            date_vid = ' '.join(date_vid.split(' ')[0:3])
                        else:
                            num_views = "0"
                            date_vid = "Date not found"
                    else:
                        num_views = "0"
                        date_vid = "Date not found"
                except:
                    num_views = "0"
                    date_vid = "Date not found"
                
                # Performance monitoring end
                stop_time = time.process_time()
                stop_time_total = time.time()
                tt = stop_time_total - start_time_total
                pt = stop_time - start_time
                mu_start_2, mu_stop_2 = tracemalloc.get_traced_memory()
                diff_mu_data = mu_stop_2 - mu_stop_1
                new_data = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
                diff_data = new_data - old_data
                tracemalloc.stop()
                
                j += 1
                data_record_table.loc[len(data_record_table.index)] = [j, tt, pt, diff_data, diff_mu_data]
                data_record_table.to_excel("scrapy_system_reading_3.xlsx", index=False)
                
                self.logger.info(f"Extracted: {title_text} | Views: {num_views} | Likes: {num_likes} | Date: {date_vid}")
                
            except Exception as e:
                self.logger.error(f"Error extracting data: {e}")
                
        except Exception as e:
            self.logger.error(f"Error processing video: {e}")
        finally:
            if driver:
                driver.quit()
        
        # Store data
        self.video_data.append({
            'video_title': title_text,
            'time_uploaded': date_vid,
            'num_views': num_views,
            'num_likes': num_likes,
        })
        
        # Save to Excel periodically
        if len(self.video_data) % 10 == 0:
            df = pd.DataFrame(self.video_data)
            df.to_excel('scrapy_knowledgebase_data.xlsx', index=False)
            self.logger.info(f"Saved {len(self.video_data)} videos to Excel")
        
        yield {
            'video_title': title_text,
            'time_uploaded': date_vid,
            'num_views': num_views,
            'num_likes': num_likes,
        }
    
    def close(self, spider, reason):
        # Final save
        if self.video_data:
            df = pd.DataFrame(self.video_data)
            df.to_excel('scrapy_knowledgebase_data.xlsx', index=False)
            self.logger.info(f"Final save: {len(self.video_data)} videos saved to scrapy_knowledgebase_data.xlsx")

# To run this spider:
# 1. Install scrapy: pip install scrapy
# 2. Create a scrapy project: scrapy startproject youtube_selenium_scraper
# 3. Place this file in: youtube_selenium_scraper/spiders/youtube_selenium_spider.py
# 4. Run: scrapy crawl youtube_selenium