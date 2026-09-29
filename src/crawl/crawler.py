import os
import sys
import time
import csv
import logging
from datetime import datetime
import urllib.robotparser
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIGURATION ---
BASE_URL = "https://www.topcv.vn"
USER_AGENT = "USTH-FDS-Project/2026 (contact: email@usth.edu.vn)"
DELAY = 3.1
RAW_DIR = "data/raw"
LOG_FILE = "data/crawl_log.csv"
IT_CATEGORY_URL = f"{BASE_URL}/tim-viec-lam-it-phan-mem-c10026"

os.makedirs(RAW_DIR, exist_ok=True)

# Set logging to DEBUG for maximum verbosity, but format it cleanly
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class TopCVCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        
        # Connection pooling optimization
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retries))
        
        # Note: Suppress noisy urllib3 debug logs
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(f"{BASE_URL}/robots.txt")
        try:
            self.rp.read()
        except Exception as e:
            logging.warning(f"Could not read robots.txt: {e}")

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(['url', 'status', 'timestamp'])

    def log_request(self, url, status):
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([url, status, datetime.now().isoformat()])

    def fetch_job_urls(self, limit):
        logging.info(f"Scanning category: {IT_CATEGORY_URL}")
        job_urls, page = [], 1
        
        while len(job_urls) < limit:
            if self.rp.mtime() > 0 and not self.rp.can_fetch(USER_AGENT, IT_CATEGORY_URL):
                logging.error("robots.txt blocked access.")
                break
                
            time.sleep(DELAY)
            try:
                res = self.session.get(f"{IT_CATEGORY_URL}?page={page}")
                self.log_request(res.url, res.status_code)
                
                if res.status_code != 200:
                    logging.error(f"HTTP Status {res.status_code} on list page.")
                    logging.debug(f"SERVER HEADERS: {dict(res.headers)}")
                    logging.debug(f"SERVER RESPONSE BODY (first 500 chars):\n{res.text[:500]}")
                    break
                    
                soup = BeautifulSoup(res.text, 'html.parser')
                links = [l['href'] for l in soup.find_all('a', href=True) if '/viec-lam/' in l['href']]
                links = list(set([l if l.startswith('http') else BASE_URL + l for l in links]))
                
                if not links:
                    logging.warning("No job links found on this page. HTML structure might have changed.")
                    break
                    
                job_urls.extend(links)
                logging.info(f"Page {page} scanned. Total URLs queued: {len(job_urls)}/{limit}")
                page += 1
                
            except requests.exceptions.RequestException as e:
                logging.exception(f"Connection error while fetching list page: {e}")
                break
            
        return list(set(job_urls))[:limit]

    def download_html(self, url):
        job_id = url.split('-')[-1].replace('.html', '').split('?')[0]
        filepath = os.path.join(RAW_DIR, f"{job_id}.html")
        
        if os.path.exists(filepath):
            return True 
            
        if self.rp.mtime() > 0 and not self.rp.can_fetch(USER_AGENT, url):
            return False

        time.sleep(DELAY)
        try:
            res = self.session.get(url, timeout=10)
            self.log_request(url, res.status_code)
            
            if res.status_code == 200:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(res.text)
                logging.info(f"Saved: {filepath}")
                return True
            else:
                logging.error(f"[FAILED] HTTP {res.status_code} at {url}")
                logging.debug(f"SERVER HEADERS: {dict(res.headers)}")
                logging.debug(f"SERVER RESPONSE BODY (first 500 chars):\n{res.text[:500]}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.exception(f"[CONNECTION ERROR] Failed to connect to {url}: {e}")
            self.log_request(url, f"EXCEPTION")
            return False

    def run(self, target_count):
        logging.info(f"Starting crawl for {target_count} jobs...")
        urls = self.fetch_job_urls(limit=target_count)
        success = sum(1 for url in urls if self.download_html(url))
        logging.info(f"Finished. Downloaded {success} HTML files.")

if __name__ == "__main__":
    crawler = TopCVCrawler()
    target = 1200 if len(sys.argv) > 1 and sys.argv[1] == "full" else 250
    crawler.run(target)