import requests
from django.conf import settings
from decimal import Decimal

def convert_currency(from_currency, to_currency, amount):
    """
    Call the currency conversion API to convert an amount from one currency to another.
    
    Args:
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        amount (Decimal): Amount to convert
        
    Returns:
        tuple: (success, result)
            success (bool): Whether the conversion was successful
            result (Decimal or str): Converted amount or error message
    """
    try:
        # Get base URL from settings or use default
        base_url = getattr(settings, 'API_BASE_URL', 'http://127.0.0.1:8000/api')
        
        # Construct the API URL
        api_url = f"{base_url}/conversion/{from_currency}/{to_currency}/{amount}/"
        
        # Make the request
        response = requests.get(api_url)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            converted_amount = Decimal(str(data['converted_amount']))
            return True, converted_amount
        else:
            # Extract error message from response
            data = response.json()
            error_message = data.get('error', f"API error: {response.status_code}")
            return False, error_message
            
    except requests.RequestException as e:
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"