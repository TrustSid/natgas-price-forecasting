import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
import warnings
import os
warnings.filterwarnings('ignore')

def load_price_data(csv_file='Nat_Gas.csv'):
    """Load and prepare natural gas price data"""
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file '{csv_file}' not found")
    
    df = pd.read_csv(csv_file)
    df['Dates'] = pd.to_datetime(df['Dates'])
    df['Prices'] = df['Prices'].astype(float)
    df['Month'] = df['Dates'].dt.month
    df['Year'] = df['Dates'].dt.year
    df['DayOfYear'] = df['Dates'].dt.dayofyear
    df['TimeIndex'] = range(len(df))
    return df

def build_price_model(df):
    """Build Fourier series-based price forecasting model"""
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
    return model

def estimate_price(date_str, model, reference_date, last_time_index):
    """Estimate price for any date using the Fourier series model (monthly data)"""
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

def price_storage_contract(injection_dates: list,
                          withdrawal_dates: list,
                          injection_volumes: list,
                          withdrawal_volumes: list,
                          csv_file: str = 'Nat_Gas.csv',
                          max_storage_capacity: float = 5000000,
                          storage_costs: dict = None) -> dict:
    """
    Price a natural gas storage contract with multiple injection/withdrawal dates
    
    Parameters:
    -----------
    injection_dates : list - list of dates when gas will be injected ['YYYY-MM-DD', ...]
    withdrawal_dates : list - list of dates when gas will be withdrawn ['YYYY-MM-DD', ...]
    injection_volumes : list - list of volumes for each injection (MMBtu)
    withdrawal_volumes : list - list of volumes for each withdrawal (MMBtu)
    csv_file : str - path to CSV file with historical price data (default: 'Nat_Gas.csv')
    max_storage_capacity : float - maximum storage capacity (MMBtu)
    storage_costs : dict - cost parameters
    
    Returns:
    --------
    dict - Contract details including value and breakdown
    """
    
    # Default storage costs if not provided
    if storage_costs is None:
        storage_costs = {
            'monthly_storage_fee': 100000,
            'injection_cost': 10,        # $ per 1 million MMBtu
            'withdrawal_cost': 10,       # $ per 1 million MMBtu
            'transport_cost_per_trip': 25000
        }
    
    # Validate inputs
    if len(injection_dates) != len(injection_volumes):
        raise ValueError("Number of injection dates must match number of injection volumes")
    
    if len(withdrawal_dates) != len(withdrawal_volumes):
        raise ValueError("Number of withdrawal dates must match number of withdrawal volumes")
    
    if len(injection_dates) == 0 or len(withdrawal_dates) == 0:
        raise ValueError("Must have at least one injection and withdrawal date")
    
    # Validate and convert dates
    try:
        injection_dates_parsed = [pd.to_datetime(date) for date in injection_dates]
        withdrawal_dates_parsed = [pd.to_datetime(date) for date in withdrawal_dates]
    except:
        raise ValueError("Invalid date format. Use 'YYYY-MM-DD' format")
    
    # Validate volumes are positive
    for volume in injection_volumes:
        if volume <= 0:
            raise ValueError(f"Injection volume {volume} must be positive")
    
    for volume in withdrawal_volumes:
        if volume <= 0:
            raise ValueError(f"Withdrawal volume {volume} must be positive")
    
    # Check if total withdrawals equal total injections
    total_injection_volume = sum(injection_volumes)
    total_withdrawal_volume = sum(withdrawal_volumes)
    
    if abs(total_injection_volume - total_withdrawal_volume) > 1e-6:  # Allow for floating point precision
        raise ValueError(f"Total injection volume ({total_injection_volume}) must equal total withdrawal volume ({total_withdrawal_volume})")
    
    # Create operations list
    operations = []
    
    # Add injection operations
    for i, (date, volume) in enumerate(zip(injection_dates_parsed, injection_volumes)):
        operations.append({
            'date': date,
            'type': 'injection',
            'volume': volume,
            'index': i
        })
    
    # Add withdrawal operations
    for i, (date, volume) in enumerate(zip(withdrawal_dates_parsed, withdrawal_volumes)):
        operations.append({
            'date': date,
            'type': 'withdrawal',
            'volume': volume,
            'index': i
        })
    
    # Sort operations by date
    operations.sort(key=lambda x: x['date'])
    
    # Check storage capacity constraints
    current_storage = 0
    for op in operations:
        if op['type'] == 'injection':
            current_storage += op['volume']
            if current_storage > max_storage_capacity:
                raise ValueError(f"Storage capacity {max_storage_capacity} exceeded by injection on {op['date']}")
        else:  # withdrawal
            current_storage -= op['volume']
            if current_storage < 0:
                raise ValueError(f"Cannot withdraw {op['volume']} on {op['date']}: insufficient storage")
    
    # Load price data and build model
    price_df = load_price_data(csv_file)
    price_model = build_price_model(price_df)
    reference_date = price_df['Dates'].iloc[-1]
    last_time_index = price_df['TimeIndex'].iloc[-1]
    
    # Helper function to get price for a date using the model
    def get_price(date_str):
        return estimate_price(date_str, price_model, reference_date, last_time_index)
    
    # Calculate cash flows
    total_purchase_cost = 0
    total_sale_revenue = 0
    total_injection_cost = 0
    total_withdrawal_cost = 0
    total_transport_cost = 0
    
    injection_details = []
    withdrawal_details = []
    
    # Process injections
    for i, (date, volume) in enumerate(zip(injection_dates, injection_volumes)):
        price = get_price(date)
        cost = volume * price
        total_purchase_cost += cost
        total_injection_cost += (volume / 1_000_000) * storage_costs['injection_cost']
        total_transport_cost += storage_costs['transport_cost_per_trip']
        
        injection_details.append({
            'date': date,
            'volume': volume,
            'price': price,
            'cost': cost
        })
    
    # Process withdrawals
    for i, (date, volume) in enumerate(zip(withdrawal_dates, withdrawal_volumes)):
        price = get_price(date)
        revenue = volume * price
        total_sale_revenue += revenue
        total_withdrawal_cost += (volume / 1_000_000) * storage_costs['withdrawal_cost']
        total_transport_cost += storage_costs['transport_cost_per_trip']
        
        withdrawal_details.append({
            'date': date,
            'volume': volume,
            'price': price,
            'revenue': revenue
        })
    
    # Calculate storage duration - from first injection to last withdrawal
    first_injection_date = min(injection_dates_parsed)
    last_withdrawal_date = max(withdrawal_dates_parsed)
    
    if last_withdrawal_date < first_injection_date:
        raise ValueError("Last withdrawal date must be after first injection date")
    
    # Calculate duration in months
    duration_months = (last_withdrawal_date.year - first_injection_date.year) * 12 + (last_withdrawal_date.month - first_injection_date.month)
    if duration_months == 0:
        duration_months = 1  # Minimum 1 month storage
    
    total_storage_cost = duration_months * storage_costs['monthly_storage_fee']
    
    # Calculate final contract value
    contract_value = (total_sale_revenue - total_purchase_cost - total_injection_cost - 
                     total_withdrawal_cost - total_transport_cost - total_storage_cost)
    
    # Return detailed results
    return {
        'contract_value': contract_value,
        'total_sale_revenue': total_sale_revenue,
        'total_purchase_cost': total_purchase_cost,
        'total_injection_cost': total_injection_cost,
        'total_withdrawal_cost': total_withdrawal_cost,
        'total_transport_cost': total_transport_cost,
        'total_storage_cost': total_storage_cost,
        'duration_months': duration_months,
        'total_volume': total_injection_volume,
        'injection_details': injection_details,
        'withdrawal_details': withdrawal_details
    }