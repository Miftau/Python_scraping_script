import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data from SQLite
def load_data(db_file='olx_data.db'):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM olx_listings", conn)
    conn.close()
    return df

# Clean price column for numeric analysis
def clean_price_column(df):
    df['price_clean'] = df['price'].str.replace(r'[^\d]', '', regex=True)
    df['price_clean'] = pd.to_numeric(df['price_clean'], errors='coerce')
    return df

# Plot 1: Top 10 Most Expensive Listings
def plot_top_expensive(df):
    top10 = df.sort_values(by='price_clean', ascending=False).head(10)
    plt.figure(figsize=(12, 6))
    sns.barplot(x='price_clean', y='title', data=top10, palette='viridis')
    plt.title('Top 10 Most Expensive Listings')
    plt.xlabel('Price (PLN)')
    plt.ylabel('Listing Title')
    plt.tight_layout()
    plt.show()

# Plot 2: Price Distribution
def plot_price_distribution(df):
    plt.figure(figsize=(10, 5))
    sns.histplot(df['price_clean'].dropna(), bins=30, kde=True, color='blue')
    plt.title('Price Distribution of Listings')
    plt.xlabel('Price (PLN)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.show()

# Plot 3: Listings by Location
def plot_listings_by_location(df):
    top_locations = df['location'].value_counts().head(10)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_locations.values, y=top_locations.index, palette='cubehelix')
    plt.title('Top 10 Locations by Number of Listings')
    plt.xlabel('Number of Listings')
    plt.ylabel('Location')
    plt.tight_layout()
    plt.show()

# Main visualizer
def main():
    df = load_data()
    df = clean_price_column(df)

    plot_top_expensive(df)
    plot_price_distribution(df)
    plot_listings_by_location(df)

if __name__ == '__main__':
    main()
