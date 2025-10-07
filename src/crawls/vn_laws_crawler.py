import requests
import os

URL = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/01/luat24.pdf"
OUTPUT_PATH= "data/raw/vn_laws/luat-24-2023-qh15.pdf"

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

response = requests.get(URL)
if response.status_code == 200:
    with open(OUTPUT_PATH, "wb") as f:
        f.write(response.content)
    print("Downloaded:", OUTPUT_PATH)
else:
    print("Failed:", response.status_code)
