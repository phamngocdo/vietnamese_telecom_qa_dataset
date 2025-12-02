import arxiv
import os
import requests
import time

from src.crawls.config import RAW_DATA_PATH

OUTPUT_DIR = os.path.join(RAW_DATA_PATH, "arxiv")

QUERY = '"4G" OR "5G" OR "6G" OR "telecommunication" OR "network slicing" OR "beamforming" OR "MIMO"'

MAX_RESULTS = 200

client = arxiv.Client(
    page_size=100,
    delay_seconds=4,
    num_retries=5
)

def crawlers():
    try:
        search = arxiv.Search(
            query=QUERY,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending,
            max_results=MAX_RESULTS
        )

        for result in client.results(search):
            title = result.title.replace(" ", "_").replace("/", "_").replace(":", "_")
            pdf_url = result.pdf_url
            pdf_path = os.path.join(OUTPUT_DIR, f"{title}.pdf")

            if os.path.exists(pdf_path):
                print(f"Skipped (already exists): {title}")
                continue

            try:
                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(pdf_path, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            pdf_file.write(chunk)

                print(f"Downloaded: {pdf_path}")
                time.sleep(1)
            except Exception as e:
                print(f"Failed to download {pdf_url}: {e}")

    except arxiv.UnexpectedEmptyPageError as e:
        print(f"Unexpected empty page: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    crawlers()