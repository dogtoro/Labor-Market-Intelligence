"""
Crawler ITviec — tải HTML thô tin tuyển dụng IT công khai.

Nguồn URL: sitemap `twinnings_jobs_desc_en.xml` (robots.txt khai báo sitemap index
`/dunggiatminh.xml`). Bản `_vn.xml` trùng 100% slug với bản EN nên chỉ dùng EN.

Quy tắc (CLAUDE.md mục 3): UA trung thực, delay ≥3s, tôn trọng robots.txt,
chỉ trang công khai, có cache (file đã tồn tại → không tải lại).

Usage:
    CRAWL_CONTACT=<email nhóm> python src/crawl/crawler.py pilot   # 20 tin ngẫu nhiên (seed cố định)
    CRAWL_CONTACT=<email nhóm> python src/crawl/crawler.py full    # toàn bộ sitemap
"""

import csv
import logging
import os
import random
import re
import sys
import time
import urllib.robotparser
from datetime import datetime, timedelta, timezone

import requests

# --- CONFIGURATION ---
BASE_URL = "https://itviec.com"
SITEMAP_INDEX_URL = f"{BASE_URL}/dunggiatminh.xml"
JOBS_SITEMAP_URL = f"{BASE_URL}/twinnings_jobs_desc_en.xml"
DELAY = 3.1
RAW_DIR = "data/raw"
SITEMAP_DIR = os.path.join(RAW_DIR, "_sitemaps")
LOG_FILE = "data/crawl_log.csv"
TZ = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh
PILOT_SIZE = 20
PILOT_SEED = 2026

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def build_user_agent():
    contact = os.environ.get("CRAWL_CONTACT", "").strip()
    if not contact or "@" not in contact:
        sys.exit("Thiếu CRAWL_CONTACT (email thật của nhóm) — UA phải có liên hệ trung thực.")
    return f"USTH-FDS-Project/2026 (contact: {contact})"


def job_id_from_url(url):
    """job_id = toàn bộ slug. KHÔNG dùng 4 số cuối: 681 tin chỉ có 612 đuôi khác nhau."""
    return url.rstrip("/").split("/")[-1]


class ITviecCrawler:
    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last_request = 0.0

        os.makedirs(SITEMAP_DIR, exist_ok=True)
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["url", "status", "timestamp"])

        # robots.txt tải bằng chính UA của dự án; không đọc được → dừng, không crawl mù
        res = self.get(f"{BASE_URL}/robots.txt")
        if res is None or res.status_code != 200:
            sys.exit("Không đọc được robots.txt — dừng crawl.")
        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.parse(res.text.splitlines())

    def log_request(self, url, status):
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([url, status, datetime.now(TZ).isoformat()])

    def get(self, url):
        """GET với delay ≥ DELAY giây kể từ request trước. Mọi request đều được log."""
        wait = DELAY - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            res = self.session.get(url, timeout=20)
            self.log_request(url, res.status_code)
            return res
        except requests.exceptions.RequestException as e:
            logging.error(f"[CONNECTION ERROR] {url}: {e}")
            self.log_request(url, "EXCEPTION")
            return None
        finally:
            self._last_request = time.time()

    def fetch_cached(self, url, path):
        """Trả về nội dung file; chỉ tải khi chưa có trong cache. None nếu lỗi."""
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
        if not self.rp.can_fetch(self.user_agent, url):
            logging.warning(f"robots.txt chặn: {url}")
            return None
        res = self.get(url)
        if res is None or res.status_code != 200:
            logging.error(f"[FAILED] HTTP {getattr(res, 'status_code', '-')} at {url}")
            return None
        with open(path, "w", encoding="utf-8") as f:
            f.write(res.text)
        return res.text

    def fetch_job_urls(self):
        xml = self.fetch_cached(JOBS_SITEMAP_URL, os.path.join(SITEMAP_DIR, "jobs_desc_en.xml"))
        if xml is None:
            sys.exit("Không tải được sitemap tin tuyển dụng — dừng crawl.")
        urls = re.findall(r"<loc>(.*?)</loc>", xml)
        logging.info(f"Sitemap: {len(urls)} tin.")
        return urls

    def run(self, mode):
        urls = self.fetch_job_urls()
        if mode == "pilot":
            random.seed(PILOT_SEED)
            urls = random.sample(urls, min(PILOT_SIZE, len(urls)))

        ok = cached = 0
        for i, url in enumerate(urls, 1):
            path = os.path.join(RAW_DIR, f"{job_id_from_url(url)}.html")
            was_cached = os.path.exists(path)
            if self.fetch_cached(url, path) is not None:
                ok += 1
                cached += was_cached
            if i % 50 == 0:
                logging.info(f"{i}/{len(urls)} xử lý xong ({ok} thành công).")
        logging.info(f"Xong: {ok}/{len(urls)} file HTML ({cached} lấy từ cache).")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    if mode not in ("pilot", "full"):
        sys.exit("Usage: python src/crawl/crawler.py [pilot|full]")
    ITviecCrawler(build_user_agent()).run(mode)
