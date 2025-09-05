import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# Load data from CSV file
def load_data(csv_file='Nat_Gas.csv'):
    df = pd.read_csv(csv_file)
    df['Dates'] = pd.to_datetime(df['Dates'])
    df['Prices'] = df['Prices'].astype(float)
    df['Month'] = df['Dates'].dt.month
    df['Year'] = df['Dates'].dt.year
    df['DayOfYear'] = df['Dates'].dt.dayofyear
    df['TimeIndex'] = range(len(df))
    
    print(f"Loaded {len(df)} data points from {df['Dates'].min().strftime('%Y-%m-%d')} to {df['Dates'].max().strftime('%Y-%m-%d')}")
    return df

# Build forecasting model
def build_model(df):
    X = np.column_stack([
        df['TimeIndex'],
        np.sin(2 * np.pi * df['DayOfYear'] / 365.25),
        np.cos(2 * np.pi * df['DayOfYear'] / 365.25),
        np.sin(4 * np.pi * df['DayOfYear'] / 365.25),
        np.cos(4 * np.pi * df['DayOfYear'] / 365.25),
        df['Month']
    ])
    y = df['Prices']
    model = LinearRegression()
    model.fit(X, y)
    print(f"Model R² score: {model.score(X, y):.3f}")
    return model

# Estimate price for any date (monthly data)
def estimate_price(date_str, model, reference_date, last_time_index):
    target_date = pd.to_datetime(date_str)
    # Calculate months difference for monthly data
    months_diff = (target_date.year - reference_date.year) * 12 + (target_date.month - reference_date.month)
    time_index = last_time_index + months_diff
    day_of_year = target_date.dayofyear
    month = target_date.month

    features = np.array([[ 
        time_index,
        np.sin(2 * np.pi * day_of_year / 365.25),
        np.cos(2 * np.pi * day_of_year / 365.25),
        np.sin(4 * np.pi * day_of_year / 365.25),
        np.cos(4 * np.pi * day_of_year / 365.25),
        month
    ]])
    price = model.predict(features)[0]
    return max(0, price)

# Main analysis function
def main():
    df = load_data('Nat_Gas.csv')
    model = build_model(df)
    return model, df

# Function to use for price estimation
def get_price_estimate(date_str, csv_file='Nat_Gas.csv'):
    df = load_data(csv_file)
    model = build_model(df)
    price = estimate_price(date_str, model, df['Dates'].iloc[-1], df['TimeIndex'].iloc[-1])
    return price

# Run the model and start interactive prompt
if __name__ == "__main__":
    model, df = main()

    print("\n" + "="*50)
    print("Interactive Price Estimation Tool")
    print("Enter dates in YYYY-MM-DD format (or 'quit' to exit)")
    print("Note: Based on monthly historical data")
    print("="*50)

    while True:
        date_input = input("\nEnter date: ").strip()
        if date_input.lower() == 'quit':
            break
        try:
            if pd.to_datetime(date_input) > datetime(2025, 9, 30):
                print("Only forecasts up to 2025-09-30 are supported.")
                continue
            price = estimate_price(date_input, model, df['Dates'].iloc[-1], df['TimeIndex'].iloc[-1])
            print(f"Estimated price for {date_input}: ${price:.2f}")
        except Exception as e:
            print(f"Error: {e}\nPlease use YYYY-MM-DD format.")