import os
from PIL import Image
import pytesseract
from PyPDF2 import PdfMerger
from io import BytesIO
import requests
import re
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import json
# Make sure to download tesseract for OCR functionality on PDF
# Function to handle sorting of pages
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def create_pdf(name):
    img_folder = "temp"
    output_pdf = f"{name}.pdf"

    image_files = sorted([
        os.path.join(img_folder, f)
        for f in os.listdir(img_folder)
        if f.lower().endswith('.webp')
    ], key=natural_sort_key)

    pdf_bytes_list = []

    for img_path in image_files:
        print(f"Processing image: {img_path}")  
        img = Image.open(img_path)
        ocr_pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
        pdf_bytes_list.append(ocr_pdf_bytes)

    merger = PdfMerger()
    for pdf_bytes in pdf_bytes_list:
        merger.append(BytesIO(pdf_bytes))

    with open(output_pdf, "wb") as f_out:
        merger.write(f_out)

    print(f"Saved searchable PDF to {output_pdf}")
    shutil.rmtree("temp")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
url = input("Please provide a issuu link starting with https: ")
r = requests.get(f"{url}", headers=headers)
try:
    json_file_url = urlunparse(urlparse(url)._replace(query=""))
    json_file_url = json_file_url.replace("issuu.com/", "reader3.isu.pub/")
    json_file_url = json_file_url.replace("docs/", "")
    json_file_url += "/reader3_4.json" 
    # print("current string: ", json_file_url)
    r=requests.get(f"{json_file_url}", headers=headers)
    r.raise_for_status()
    content = r.json()
    with open ("dump.json", "w", encoding="utf-8") as f:
       json.dump(content, f, ensure_ascii=False, indent=4)
    
    os.makedirs("temp", exist_ok=True)
    with open("dump.json", "r", encoding='utf-8') as f:
        data = json.load(f)
        for i, page in enumerate(data['document']['pages']):
            image_url = "https://" + page['imageUri']
            image_request = requests.get(image_url)
            filename = f"temp/page_{i+1}.webp" 
            with open(filename, 'wb') as out_file:
                out_file.write(image_request.content)
                print(f"Downloading... {page['imageUri']}", )
    pattern = r'https://reader3\.isu\.pub/([^/]+)/([^/]+)'
    match = re.search(pattern, json_file_url)
    name = ""
    if match:
        name = match.group(2)
    else:
        name = "output"
        print("couldn't find a name, going with default name output")
    create_pdf(name)

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err} - Status code: {response.status_code}")
except requests.exceptions.RequestException as err:
    print(f"Other error occurred: {err}")
