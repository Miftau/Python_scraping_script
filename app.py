from flask import Flask, render_template_string, request, send_file
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
from urllib.parse import urljoin
import uuid
import re
from fpdf import FPDF
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

app = Flask(__name__)

# Bootstrap HTML Template (unchanged)
template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Universal Web Scraper</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="card shadow p-4">
        <h2 class="text-center mb-4">Progress Web Scraper</h2>
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Website URL</label>
                <input name="url" type="url" class="form-control" placeholder="https://example.com" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Keyword (e.g., phone, car, land)</label>
                <input name="keyword" type="text" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Export Format</label>
                <select name="format" class="form-select">
                    <option value="csv">CSV</option>
                    <option value="excel">Excel</option>
                    <option value="pdf">PDF</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary w-100">Scrape & Download</button>
        </form>
    </div>
</div>
</body>
</html>
"""


def clean_price(text):
    """
    Clean and validate price text, ensuring it matches common price formats.
    """
    if not text:
        return 'N/A'
    # Match prices like ₦1,000, $50.99, €1,234.56, 1000, NGN 1,000.00, or USD 50
    price_pattern = r'(?:[\₦\$\€]|NGN|USD|EUR|GBP)?\s*[\d,]+(?:\.\d{1,2})?\b'
    match = re.search(price_pattern, str(text), re.IGNORECASE)
    if match:
        price = match.group().strip()
        # Exclude ratings or similar (e.g., 4.5, 5.0)
        if re.match(r'^\d+\.\d{1,2}$', price):
            return 'N/A'
        return price
    return 'N/A'


def scrape_with_selenium(base_url, keyword, max_pages=5):
    """
    Scrape dynamic websites using Selenium for JavaScript-rendered content.
    """
    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)

    all_data = []
    url = base_url

    for _ in range(max_pages):
        try:
            driver.get(url)
            # Wait for dynamic content to load (up to 10 seconds)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract potential listings
            for elem in soup.find_all(['div', 'article', 'section']):
                text = elem.get_text(strip=True).lower()
                if keyword.lower() in text:
                    title = elem.find(['h2', 'h3', 'h6'])
                    # Look for price in elements with price-related classes or tags
                    price_elem = None
                    for candidate in elem.find_all(['span', 'div', 'p', 'strong', 'b']):
                        candidate_text = candidate.get_text(strip=True).lower()
                        candidate_classes = candidate.get('class', [])
                        # Check for price-related classes or keywords
                        if any(k in candidate_classes for k in ['price', 'cost', 'amount', 'value', 'prc']):
                            price_elem = candidate
                            break
                        if re.search(r'(?:price|cost|amount|value|for\s+sale)', candidate_text, re.IGNORECASE):
                            price_elem = candidate
                            break
                    # Fallback: search for price pattern in element or nearby text
                    if not price_elem:
                        price_elem = elem.find(
                            string=re.compile(r'(?:[\₦\$\€]|NGN|USD|EUR|GBP)?\s*[\d,]+(?:\.\d{1,2})?\b', re.IGNORECASE))
                    link = elem.find('a', href=True)

                    all_data.append({
                        "id": str(uuid.uuid4()),
                        "title": title.text.strip() if title else "N/A",
                        "price": clean_price(price_elem) if price_elem else "N/A",
                        "url": urljoin(base_url, link['href']) if link else "N/A"
                    })

            # Try to find next page
            next_link = soup.find('a', string=re.compile("next", re.IGNORECASE))
            if next_link and 'href' in next_link.attrs:
                url = urljoin(base_url, next_link['href'])
            else:
                break

        except TimeoutException:
            print(f"Timeout loading {url}")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    driver.quit()
    return pd.DataFrame(all_data)


def scrape_with_requests(base_url, keyword, max_pages=5):
    """
    Scrape static websites using requests and BeautifulSoup.
    """
    session = requests.Session()
    url = base_url
    all_data = []

    for _ in range(max_pages):
        try:
            res = session.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            for elem in soup.find_all(['div', 'article', 'section']):
                text = elem.get_text(strip=True).lower()
                if keyword.lower() in text:
                    title = elem.find(['h2', 'h3', 'h6'])
                    price_elem = None
                    for candidate in elem.find_all(['span', 'div', 'p', 'strong', 'b']):
                        candidate_text = candidate.get_text(strip=True).lower()
                        candidate_classes = candidate.get('class', [])
                        if any(k in candidate_classes for k in ['price', 'cost', 'amount', 'value', 'prc']):
                            price_elem = candidate
                            break
                        if re.search(r'(?:price|cost|amount|value|for\s+sale)', candidate_text, re.IGNORECASE):
                            price_elem = candidate
                            break
                    if not price_elem:
                        price_elem = elem.find(
                            string=re.compile(r'(?:[\₦\$\€]|NGN|USD|EUR|GBP)?\s*[\d,]+(?:\.\d{1,2})?\b', re.IGNORECASE))
                    link = elem.find('a', href=True)

                    all_data.append({
                        "id": str(uuid.uuid4()),
                        "title": title.text.strip() if title else "N/A",
                        "price": clean_price(price_elem) if price_elem else "N/A",
                        "url": urljoin(base_url, link['href']) if link else "N/A"
                    })

            next_link = soup.find('a', string=re.compile("next", re.IGNORECASE))
            if next_link and 'href' in next_link.attrs:
                url = urljoin(base_url, next_link['href'])
            else:
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    return pd.DataFrame(all_data)


def scrape_site(base_url, keyword, max_pages=5):
    """
    Attempt to scrape with Selenium first, fall back to requests if it fails.
    """
    try:
        df = scrape_with_selenium(base_url, keyword, max_pages)
        if not df.empty:
            return df
    except Exception as e:
        print(f"Selenium failed: {e}, falling back to requests")

    return scrape_with_requests(base_url, keyword, max_pages)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        keyword = request.form['keyword']
        file_format = request.form['format']

        df = scrape_site(url, keyword)

        if df.empty:
            return "No data found. Try a different URL or keyword."

        buffer = BytesIO()
        if file_format == 'csv':
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='data.csv', mimetype='text/csv')

        elif file_format == 'excel':
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ScrapedData')
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='data.xlsx',
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        elif file_format == 'pdf':
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for i, row in df.iterrows():
                pdf.cell(200, 10, txt=f"{row['title']} - {row['price']}", ln=1)
            pdf.output(buffer)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='scrape_data.pdf', mimetype='application/pdf')

    return render_template_string(template)


if __name__ == '__main__':
    app.run(debug=True)