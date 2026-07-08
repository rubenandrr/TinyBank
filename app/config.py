"""
This module contains the basic bank configurations, including reference exchange rates
fetched dynamically via API, the currency exchange commission margin, and default daily limits.
"""

import httpx # type: ignore

# Fallback exchange rates (used if the external API is offline)
DEFAULT_EXCHANGE_RATES = {
    "EUR": 1.0,
    "CHF": 0.96,  # 1 EUR = 0.96 CHF
    "USD": 1.08,  # 1 EUR = 1.08 USD
}

def fetch_live_rates() -> dict:
    """
    Fetches real-time exchange rates from the free public API open.er-api.com.
    Returns the fallback rates in case of network timeout or issues.
    """
    url = "https://open.er-api.com/v6/latest/EUR"
    try:
        # 2.0-second timeout to avoid blocking startup
        response = httpx.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            # Extract only the currencies handled by Tiny Bank
            return {
                "EUR": float(rates.get("EUR", 1.0)),
                "CHF": float(rates.get("CHF", 0.96)),
                "USD": float(rates.get("USD", 1.08)),
            }
    except Exception as e:
        print(f"Warning: Failed to fetch live exchange rates ({e}). Using static fallback rates.")
    
    return DEFAULT_EXCHANGE_RATES

# Load dynamic exchange rates on application startup
EXCHANGE_RATES = fetch_live_rates()

# Banking commission fee charged during multi-currency transactions (0.5%)
BANK_MARGIN = 0.005  

# Default daily limits for new accounts
DEFAULT_DAILY_WITHDRAWAL_LIMIT = 1000.0
DEFAULT_DAILY_TRANSFER_LIMIT = 5000.0
DEFAULT_MAX_DAILY_TRANSFERS = 5