🏠 OLX Real Estate Listings Scraper – Żywiec, Poland
This project is a Python-based web scraper designed to extract real estate listings from OLX Poland for Plots and Apartments in Żywiec. It collects key data points such as title, price, location, date posted, and listing URL. The data is saved to both CSV and SQLite formats and supports further analysis with visualizations.

📦 Features
Scrapes OLX listings from multiple category pages
Extracts:
Title
Price
Location
Date Posted
URL
Category
Saves data to:
CSV file: olx_zywiec_listings.csv
SQLite DB: olx_data.db
Counts number of listings in Żywiec
Includes a visualization script to:
Show most expensive listings
Price distribution
Category-wise statistics
Price per square meter (if extended)
🛠️ Setup & Installation
1. Clone the repository
git clone https://github.com/Miftau/Python_scraping_script
cd ads_scraper
2. Install dependencies
pip install -r requirements.txt
Dependencies include:

requests
beautifulsoup4
pandas
matplotlib
sqlite3 (built-in)
3. Run the scraper
python olx_scraper.py
This will create:

olx_zywiec_listings.csv
olx_data.db (SQLite database)
📊 Run Visual Analysis
python visual.py
This will:

Load listings from the SQLite database
Plot graphs like:
Top 10 most expensive listings
Price distribution histogram
Listings count by category
📁 Project Structure
olx-zywiec-scraper/
│
├── olx_scraper.py         # Scrapes listings and saves to DB/CSV
├── visual.py              # Analyzes and visualizes listing data
├── olx_data.db            # SQLite database (auto-generated)
├── olx_zywiec_listings.csv# CSV file (auto-generated)
├── README.md              # You are here!
└── requirements.txt       # Project dependencies
✅ To Do
Add support for more cities
Extract square meter data (to calculate price/m²)
Add filters (e.g., max price, posted today)
Deploy as a web app with search interface
📜 License
This project is licensed under the MIT License. See LICENSE for details.
