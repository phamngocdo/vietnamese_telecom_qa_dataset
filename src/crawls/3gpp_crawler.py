from scrapy import Spider, Request
from scrapy.pipelines.files import FilesPipeline
from urllib.parse import urljoin
from typing import override
import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.file_helpers import extract_nested_zip, convert_doc_to_pdf

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
                                info.spider.logger.error(f"Failed to convert {doc_path} to PDF: {e}")

        return item
    
    @override
    def close_spider(self, spider):
        zip_folder = spider.settings.get('FILES_STORE')
        if os.path.exists(zip_folder):
            try:
                shutil.rmtree(zip_folder)
                spider.logger.info(f"Deleted zip folder: {zip_folder}")
            except Exception as e:
                spider.logger.error(f"Failed to delete zip folder: {e}")

class ThreeGPPSpider(Spider):
    name = "threegpp"
    allowed_domains = ["3gpp.org"]

    releases = [f"Rel-{i}" for i in [17]] #15-18
    series_list = [f"{i}_series" for i in [29]]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 2,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.5993.90 Safari/537.36",
        "ROBOTSTXT_OBEY": True,
        "FILES_STORE": "downloaded_zips",
        "ITEM_PIPELINES": {
            '__main__.ThreeGPPFilesPipeline': 1,
        },

        "DOWNLOAD_FAIL_ON_DATALOSS": False,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408],
        "DOWNLOAD_TIMEOUT": 120,
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    @override
    def start_requests(self):
        for release in self.releases:
            for series in self.series_list:
                url = f"https://www.3gpp.org/ftp/Specs/latest/{release}/{series}/"
                yield Request(url, callback=self.parse)

    @override
    def parse(self, response):
        release = response.url.split("/")[-3]
        series = response.url.split("/")[-2]

        for file_link in response.css("a::attr(href)").getall():
            if file_link.endswith(".zip"):
                file_url = urljoin(response.url, file_link)
                file_name = os.path.basename(file_link)
                extract_path = os.path.join("data/raw/3gpp_spec/", release, series, file_name.replace(".zip",""))
                os.makedirs(extract_path, exist_ok=True)

                yield {
                    "file_name": file_name,
                    "file_urls": [file_url],
                    "release": release,
                    "series": series,
                    "extract_path": extract_path,
                }

if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess()
    process.crawl(ThreeGPPSpider)
    process.start()