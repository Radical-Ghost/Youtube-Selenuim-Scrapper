## YouTube Selenium Scraper

This project uses Scrapy and Selenium to scrape video data from a YouTube channel and save it to Excel.

### Setup

1. **Clone or download this repository.**
2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
3. **Download ChromeDriver:**

    - Find your Chrome browser version by visiting `chrome://settings/help` in Chrome.
    - Download the matching ChromeDriver from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads).
    - Place `chromedriver.exe` in your project folder (e.g., `../youtube_selenium_scraper`).
    - Alternatively, add the folder containing `chromedriver.exe` to your system PATH in Environment Variables.

4. **Create a Scrapy project (if not already done):**
    ```sh
    scrapy startproject youtube_selenium_scraper
    ```
5. **Place the spider file:**
    - Copy `youtube_spider_scrapy_try.py` into `youtube_selenium_scraper/spiders/`.

### Running the Scraper

Run the following command from your project directory:

```sh
scrapy crawl youtube_selenium
```

### Output

-   Extracted video data will be saved to `scrapy_knowledgebase_data.xlsx`.
-   Performance metrics will be saved to `scrapy_system_reading_3.xlsx`.

---

## Requirements

See `requirements.txt` for Python dependencies.
