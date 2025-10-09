from scrapy import Spider, Request
from scrapy.pipelines.files import FilesPipeline
from typing import override
import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

ITU_SERIES = {
    "G": [
        *[str(i) for i in range(1000, 1040)],  # G.1000–G.1039: QoS framework, QoE, transmission
        *[str(i) for i in range(107, 120)]     # G.107–G.119: E-model, voice QoS, delay limits
    ],
    "P": [
        *[str(i) for i in range(800, 811)],    # P.800–P.810: MOS, subjective audio tests
        *[str(i) for i in range(820, 891)],    # P.820–P.890: subjective audio/video QoE
        *[str(i) for i in range(900, 951)],    # P.900–P.950: multimedia QoE, perceptual evaluation
        "1201","1202","1203","1204","1205","1206","1301","1401","1501"  # P.1201–1501: advanced video QoE
    ],
    "Y": [
        *[str(i) for i in range(3100, 3183)],  # Y.3100–Y.3182: 5G architecture, network slicing, ML/AI in networks
        *[str(i) for i in range(3300, 3351)],  # Y.3300–Y.3350: SDN, NFV, softwarization
    ],
    "M": [
        *[str(i) for i in range(2101, 2104)],  # M.2101–2103: IMT-2020 detailed performance
    ],
    "X": [
        *[str(i) for i in range(800, 805)],    # X.800–X.804: network security architecture
        "1036"                                 # X-series: security frameworks, cloud security
    ]
}

class ItuFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        series = item.get("series", "unknown_series")
        number = item.get("number", "unknown_number")

        filename = f"{series}.{number}.pdf"

        path = os.path.join(series, number, filename)
        return path

class ItuSpider(Spider):
    name = "itu"
    allowed_domains = ["www.itu.int"]

    custom_settings = {
        "FILES_STORE": "data/raw/itu_spec/",
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS": 2,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.5993.90 Safari/537.36"
        ),
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_FAIL_ON_DATALOSS": False,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408],
        "DOWNLOAD_TIMEOUT": 120,
        "ITEM_PIPELINES": {
            "__main__.ItuFilesPipeline": 1
        },
    }

    @override
    def start_requests(self):
        for series, numbers in ITU_SERIES.items():
            for number in numbers:
                url = f"https://www.itu.int/rec/T-REC-{series}.{number}/en"
                yield Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        rec_links = response.xpath('//a[contains(@href,"T-REC")]/@href').getall()
        rec_links = [response.urljoin(link) for link in rec_links]

        self.logger.info(f"Found {len(rec_links)} recommendation links on {response.url}")

        for link in rec_links:
            yield Request(
                link,
                callback=self.parse_pdf,
                meta={"source_url": response.url},
                dont_filter=True
            )

    def parse_pdf(self, response):
        pdf_links = response.xpath('//a[contains(@href,"lang=e") and contains(., "PDF")]/@href').getall()
        pdf_links = [response.urljoin(link) for link in pdf_links]

        self.logger.info(f"Found {len(pdf_links)} PDF-E files on {response.url}")

        series, number = None, None
        m = re.search(r"T-REC-([A-Z])\.(\d+)", response.url)
        if m:
            series = m.group(1)
            number = m.group(2)

        for link in pdf_links:
            yield {
                "file_urls": [link],
                "series": series,
                "number": number,
                "language": "en",
                "source_url": response.meta.get("source_url"),
            }

if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess
    process = CrawlerProcess()
    process.crawl(ItuSpider)
    process.start()