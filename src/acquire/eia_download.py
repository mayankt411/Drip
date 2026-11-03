"""
eia_download.py - EIA API v2 Cushing Weekly Stocks Acquisition

Retrieves weekly ending stocks of crude oil excluding SPR for Cushing, OK.
Endpoint: https://api.eia.gov/v2/petroleum/stoc/wstk/data/
"""

import os
import requests
from datetime import datetime

EIA_SERIES_ID = "WCRSTUS1" # Cushing, OK Ending Stocks excluding SPR of Crude Oil (Thousand Barrels)

def build_eia_request(api_key, start_date=None, end_date=None):
    base_url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
    params = {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[process][]": "SAE",
        "facets[duoarea][]": "NUS_WTT_1",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000
    }
    return base_url, params
