from scrapy import Spider
from scrapy.pipelines.files import FilesPipeline
from typing import override
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.file_helpers import convert_doc_to_pdf
from src.crawls.config import RAW_DATA_PATH

OUTPUT_DIR = os.path.join(RAW_DATA_PATH, "vn_spec")

class VnSpecFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return os.path.basename(request.url)

    @override
    def item_completed(self, results, item, info):
        for success, file_info in results:
            if not success:
                continue

            file_path = file_info["path"]
            full_path = os.path.join(info.spider.settings.get("FILES_STORE"), file_path)

            if full_path.endswith((".doc", ".docx")):
                pdf_path = os.path.splitext(full_path)[0] + ".pdf"
                try:
                    convert_doc_to_pdf(full_path, pdf_path)
                    os.remove(full_path)
                    info.spider.logger.info(f"Converted {full_path} → {pdf_path}")
                except Exception as e:
                    info.spider.logger.error(f"Failed to convert {full_path} to PDF: {e}")

        return item


class VnSpecSpider(Spider):
    name = "mst"
    allowed_domains = ["mst.gov.vn", "mic.mediacdn.vn"]
    start_urls = [
        "https://mst.gov.vn/quy-chuan-ky-thuat-quoc-gia-do-bo-tttt-ban-hanh-197240417160723563.htm"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 2,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.5993.90 Safari/537.36"
        ),
        "ROBOTSTXT_OBEY": True,
        "MEDIA_ALLOW_REDIRECTS": True,
        "REDIRECT_ENABLED": True,
        "FILES_STORE": OUTPUT_DIR,
        "ITEM_PIPELINES": {
            "__main__.VnSpecFilesPipeline": 1,
        },
        "DOWNLOAD_FAIL_ON_DATALOSS": False,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408],
        "DOWNLOAD_TIMEOUT": 120,
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    @override
    def parse(self, response):
        for a in response.css("p.MsoNormal a"):
            file_url = a.attrib.get("href")
            title = a.css("span::text").get(default="").strip()

            if file_url and file_url.endswith((".doc", ".docx", ".pdf")):
                absolute_url = response.urljoin(file_url)
                self.logger.info(f"Found file: {absolute_url}")
                yield {
                    "title": title,
                    "file_urls": [absolute_url],
                }


if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess()
    process.crawl(VnSpecSpider)
    process.start()
