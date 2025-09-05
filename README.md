# Natural Gas Price Forecasting & Storage Contract Valuation

This project provides a **Fourier series–based linear regression model** for forecasting natural gas prices and a **storage contract pricing engine** that models multi-period injections/withdrawals, enforces capacity constraints, and computes detailed cash flows. It is designed to support **risk analysis** and **trading decision-making** in energy markets.

---

## Features

- 📈 **Natural Gas Price Forecasting**
  - Uses **Fourier series (seasonality)** and time-based regressors to model price trends.
  - Forecasts future prices for user-specified dates.
  - Interactive CLI tool for quick estimation.

- 🛢️ **Storage Contract Valuation**
  - Models **gas injections and withdrawals** across multiple periods.
  - Enforces **capacity constraints** to prevent over/under storage.
  - Computes **cash flows**:
    - Purchase costs
    - Sale revenues
    - Injection & withdrawal fees
    - Transport costs
    - Monthly storage fees
  - Outputs net **contract value** with detailed breakdowns.

---

## Project Structure

```
.
├── forecasting.py        # Fourier series price forecasting tool
├── storage_contract.py   # Storage contract valuation engine
├── Nat_Gas.csv           # Historical monthly price dataset (Dates, Prices)
└── README.md
```

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/natural-gas-forecasting-storage-valuation.git
cd natural-gas-forecasting-storage-valuation
pip install -r requirements.txt
```

Dependencies:
- Python 3.8+
- pandas
- numpy
- scikit-learn

---

## Usage

### 1. Forecast Natural Gas Prices

Run the forecasting script:

```bash
python forecasting.py
```

Interactive prompt:

```
==================================================
Interactive Price Estimation Tool
Enter dates in YYYY-MM-DD format (or 'quit' to exit)
Note: Based on monthly historical data
==================================================

Enter date: 2025-07-01
Estimated price for 2025-07-01: $3.42
```

Or programmatically:

```python
from forecasting import get_price_estimate

price = get_price_estimate("2025-07-01", csv_file="Nat_Gas.csv")
print(f"Forecasted price: ${price:.2f}")
```

---

### 2. Value a Storage Contract

Example:

```python
from storage_contract import price_storage_contract

results = price_storage_contract(
    injection_dates=["2025-01-01", "2025-03-01"],
    withdrawal_dates=["2025-06-01", "2025-08-01"],
    injection_volumes=[2_000_000, 3_000_000],   # MMBtu
    withdrawal_volumes=[2_000_000, 3_000_000], # MMBtu
    csv_file="Nat_Gas.csv"
)

print("Contract Value:", results["contract_value"])
print("Breakdown:", results)
```

Output:

```
Contract Value: $1,250,000
Breakdown: {
  'total_sale_revenue': ...,
  'total_purchase_cost': ...,
  'total_storage_cost': ...,
  ...
}
```

---

## Configuration

Default **cost parameters** (can be overridden):

```python
storage_costs = {
    "monthly_storage_fee": 100000,
    "injection_cost": 10,       # per 1M MMBtu
    "withdrawal_cost": 10,      # per 1M MMBtu
    "transport_cost_per_trip": 25000
}
```

---

## Dataset

- Expected input file: `Nat_Gas.csv`
- Format:

| Dates       | Prices |
|-------------|--------|
| 2020-01-01  | 2.45   |
| 2020-02-01  | 2.10   |
| ...         | ...    |

---

## Roadmap

- [ ] Extend forecasting with ARIMA / Prophet
- [ ] Add Monte Carlo scenario generation
- [ ] Incorporate stochastic volatility
- [ ] Build dashboard with Plotly/Dash

---

## License

MIT License © 2025  
