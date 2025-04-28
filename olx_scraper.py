import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import uuid
import sqlite3
from urllib.parse import urljoin
import matplotlib.pyplot as plt
import seaborn as sns

# Headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def scrape_page(url, session):
    """Scrape a single OLX page and extract listing data."""
    listings = []
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate all listing containers
        listing_elements = soup.select('div[data-testid="listing-grid"] > div')  # Container for listings

        for listing in listing_elements:
            try:
                # Title
                title_elem = listing.select_one('h6')
                title = title_elem.text.strip() if title_elem else 'N/A'

                # Price
                price_elem = listing.select_one('p[data-testid="ad-price"]')
                price = price_elem.text.strip() if price_elem else 'N/A'

                # Location and date
                location_date_elem = listing.select_one('p[data-testid="location-date"]')
                location, date_posted = 'N/A', 'N/A'
                if location_date_elem:
                    parts = location_date_elem.text.strip().split(' - ')
                    if len(parts) == 2:
                        location, date_posted = parts

                # URL
                url_elem = listing.select_one('a[href*="/oferta/"]')
                listing_url = urljoin(url, url_elem['href']) if url_elem else 'N/A'

                listings.append({
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'price': price,
                    'location': location,
                    'date_posted': date_posted,
                    'url': listing_url
                })

            except Exception as e:
                print(f"Error processing listing: {e}")
                continue

        # Next page
        next_page = soup.select_one('a[data-testid="pagination-forward"]')
        next_page_url = urljoin(url, next_page['href']) if next_page else None

        return listings, next_page_url

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {url}: {e}")
        return [], None


def scrape_category(base_url, category_name):
    """Scrape all pages from a category."""
    all_listings = []
    url = base_url
    session = requests.Session()
    page_count = 0

    while url:
        print(f"Scraping {category_name} page: {url}")
        listings, next_page_url = scrape_page(url, session)
        for listing in listings:
            listing['category'] = category_name
        all_listings.extend(listings)
        url = next_page_url
        page_count += 1
        time.sleep(2)

        # Optional limit for testing
        if page_count >= 10 and False:
            print(f"Stopping after {page_count} pages for testing.")
            break

    return all_listings


def save_to_sqlite(df, db_file='olx_data.db'):
    """Save DataFrame to SQLite database."""
    conn = sqlite3.connect(db_file)
    df.to_sql('olx_listings', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
    print(f"Data saved to SQLite database: {db_file}")


def main():
    # Define categories
    categories = {
        'Plots': 'https://www.olx.pl/nieruchomosci/dzialki/sprzedaz/zywiec/',
        'Apartments': 'https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/zywiec/'
    }

    all_listings = []

    for category_name, base_url in categories.items():
        print(f"\nStarting scrape for category: {category_name}")
        listings = scrape_category(base_url, category_name)
        all_listings.extend(listings)

    df = pd.DataFrame(all_listings)

    # Count listings with 'Żywiec' in location
    zywiec_count = df['location'].str.contains('Żywiec', case=False, na=False).sum()
    print(f"\nNumber of listings with 'Żywiec' in location: {zywiec_count}")

    # Save to CSV and SQLite
    csv_file = 'olx_zywiec_listings.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"Data saved to CSV: {csv_file}")

    save_to_sqlite(df)

    # Print summary
    print(f"\nTotal listings scraped: {len(df)}")
    print(f"Plots: {len(df[df['category'] == 'Plots'])}")
    print(f"Apartments: {len(df[df['category'] == 'Apartments'])}")


if __name__ == '__main__':
    main()
