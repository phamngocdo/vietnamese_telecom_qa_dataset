from scrapy import Spider, Request
from scrapy.pipelines.files import FilesPipeline
from urllib.parse import urljoin
from typing import override
import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.file_helpers import extract_nested_zip, convert_doc_to_pdf
from utils.logger import *
from config import RAW_DATA_PATH

OUTPUT_DIR = os.path.join(RAW_DATA_PATH, "3gpp_spec")

RELEASES = [f"Rel-{i}" for i in [15, 16, 17, 18]]

SERIES_LIST = [
    f"{i}_series"
    for i in [
        21,  # Overview, terminology
        22,  # Service requirements
        23,  # Architecture
        24,  # Protocols / IMS
        26,  # Media & QoE
        27,  # Data services
        28,  # OAM / KPIs
        29,  # Core & interfaces
        32,  # Management & KPIs
        33,  # Security
        36,  # LTE baseline
        37,  # Multi-RAT coordination
        38,  # 5G NR
        39   # Test specs / KPIs
    ]
]

IMPORTANT_TS = [
    # --- Series 22: Service Requirements ---
    "22.261", "22.104", "22.263", "22.278", "22.281",

    # --- Series 23: Architecture & System ---
    "23.003", "23.060", "23.401", "23.501", "23.502", "23.503", "23.548",

    # --- Series 24: Protocols / IMS ---
    "24.501", "24.502", "24.503",

    # --- Series 26: Media / QoE ---
    "26.114", "26.235", "26.244",

    # --- Series 27: Data services ---
    "27.007", "27.060",

    # --- Series 28: OAM / Performance management ---
    "28.104", "28.105", "28.106", "28.550", "28.552",

    # --- Series 29: Core & Interface ---
    "29.500", "29.501", "29.502", "29.503", "29.510", "29.571",

    # --- Series 32: Management & KPIs ---
    "32.101", "32.106", "32.500", "32.501", "32.552",

    # --- Series 33: Security ---
    "33.102", "33.210", "33.401", "33.501", "33.510",

    # --- Series 36: LTE baseline (4G) ---
    "36.300", "36.331", "36.413",

    # --- Series 38: 5G NR ---
    "38.104", "38.211", "38.212", "38.213", "38.214",
    "38.300", "38.301", "38.304", "38.321", "38.322",
    "38.323", "38.331", "38.401", "38.410", "38.413",

    # --- Series 39: Test specs & KPIs ---
    "39.900", "39.910", "39.912"
]

class ThreeGPPFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        file_name = os.path.basename(request.url)
        release = item.get("release")
        series = item.get("series")
        return os.path.join(release, series, file_name)

    @override
    def item_completed(self, results, item, info):
        for success, file_info in results:
            if success:
                file_path = file_info['path']
                full_path = os.path.join(info.spider.settings.get('FILES_STORE'), file_path)
                extract_path = item.get("extract_path")
                os.makedirs(extract_path, exist_ok=True)

                extract_nested_zip(full_path, extract_path)

                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        if not file.endswith((".doc", ".docx")):
                            os.remove(os.path.join(root, file))

                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        if not os.listdir(dir_path):
                            shutil.rmtree(dir_path)

                for root, _, files in os.walk(extract_path):
                    for file in files:
                        if file.endswith((".doc", ".docx")):
                            doc_path = os.path.join(root, file)
                            pdf_path = os.path.splitext(doc_path)[0] + ".pdf"
                            try:
                                convert_doc_to_pdf(doc_path, pdf_path)
                                os.remove(doc_path)
                            except Exception as e:
                                log_error(f"Failed to convert {doc_path} to PDF: {e}")

        return item
    
    @override
    def close_spider(self, spider):
        zip_folder = spider.settings.get('FILES_STORE')
        if os.path.exists(zip_folder):
            try:
                shutil.rmtree(zip_folder)
                log_info(f"Deleted zip folder: {zip_folder}")
            except Exception as e:
                log_error(f"Failed to delete zip folder: {e}")

class ThreeGPPSpider(Spider):
    name = "threegpp"
    allowed_domains = ["3gpp.org"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 2,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.5993.90 Safari/537.36"
        ),
        "ROBOTSTXT_OBEY": True,
        "FILES_STORE": "downloaded_zips",
        "ITEM_PIPELINES": {
            "__main__.ThreeGPPFilesPipeline": 1,
        },
        "DOWNLOAD_FAIL_ON_DATALOSS": False,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408],
        "DOWNLOAD_TIMEOUT": 120,
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    @override
    def start_requests(self):
        for release in RELEASES:
            for series in SERIES_LIST:
                url = f"https://www.3gpp.org/ftp/Specs/latest/{release}/{series}/"
                yield Request(url, callback=self.parse, errback=self.errback_log, dont_filter=True)

    @override
    def parse(self, response):
        release = response.url.split("/")[-3]
        series = response.url.split("/")[-2]

        file_links = response.xpath("//a[contains(@href, '.zip')]/@href").getall()
        log_info(f"Found {len(file_links)} zip files in {release}/{series}")

        for file_link in file_links:
            file_name = os.path.basename(file_link).lower()

            if not any(ts.replace(".", "") in file_name for ts in IMPORTANT_TS):
                continue

            file_url = urljoin(response.url, file_link)
            extract_path = os.path.join(
                OUTPUT_DIR,
                release,
                series,
                file_name.replace(".zip", "")
            )
            os.makedirs(extract_path, exist_ok=True)

            yield {
                "file_name": file_name,
                "file_urls": [file_url],
                "release": release,
                "series": series,
                "extract_path": extract_path,
            }

    def errback_log(self, failure):
        log_warning(f"Request failed: {failure.request.url} — {repr(failure.value)}")
    
if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess()
    process.crawl(ThreeGPPSpider)
    log_info("Starting crawl data from 3GPP Standards")
    process.start()