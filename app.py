import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import uuid
import re

headers = {
    'User-Agent': 'Mozilla/5.0'
}


def extract_price(text):
    match = re.search(r'(\$\s?|\€\s?|\₦\s?|\₹\s?|\£\s?)?\d{1,3}(?:[,.\s]?\d{3})*(?:\.\d{2})?', text)
    return match.group(0) if match else 'N/A'


def extract_location(text):
    # Heuristic: Look for place names or keywords like "street", "road", or local city names
    location_keywords = ['street', 'road', 'avenue', 'Żywiec', 'Warsaw', 'Lagos', 'London']
    for word in location_keywords:
        if word.lower() in text.lower():
            return word
    return 'N/A'


def extract_date(text):
    # Heuristic: Look for words like "today", or date formats like "12 May 2025"
    if 'today' in text.lower() or 'dzisiaj' in text.lower():
        return 'Today'
    match = re.search(r'\d{1,2} [a-zA-Z]+ \d{4}', text)  # e.g., 12 May 2025
    return match.group(0) if match else 'N/A'


def scrape_listings(url, keyword, session):
    listings = []

    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Heuristic: Get common listing containers
        containers = soup.find_all(['div', 'li'], recursive=True)

        for item in containers:
            text_content = item.get_text(separator=' ', strip=True)
            if keyword.lower() not in text_content.lower():
                continue

            title_elem = item.find(['h1', 'h2', 'h3', 'a'])
            title = title_elem.get_text(strip=True) if title_elem else 'N/A'

            price = extract_price(text_content)
            location = extract_location(text_content)
            date_posted = extract_date(text_content)

            link_tag = item.find('a', href=True)
            full_url = urljoin(url, link_tag['href']) if link_tag else 'N/A'

            listings.append({
                'id': str(uuid.uuid4()),
                'title': title,
                'price': price,
                'location': location,
                'date_posted': date_posted,
                'url': full_url
            })

        return listings

    except Exception as e:
        print(f"Error: {e}")
        return []


def main():
    base_url = input("Enter e-commerce page URL: ").strip()
    keyword = input("Enter product keyword (e.g., shoes, laptop): ").strip()

    session = requests.Session()
    print(f"\nScraping: {base_url} for keyword: '{keyword}'...")

    results = scrape_listings(base_url, keyword, session)
    df = pd.DataFrame(results, columns=[
        'id', 'title', 'price', 'location', 'date_posted', 'url'
    ])

    if df.empty:
        print("No listings found.")
    else:
        filename = f"ecommerce_scraped_{keyword.lower()}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n✅ Scraped {len(df)} listings. Saved to: {filename}")
        print(df.head())  # Display sample

if __name__ == '__main__':
    main()
