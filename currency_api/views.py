from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
import json

# Dictionary of supported currencies and their rates against GBP
CURRENCY_RATES = {
    'GBP': 1.0,
    'USD': 1.28,
    'EUR': 1.17,
}

@api_view(['GET'])
def currency_conversion(request, currency1, currency2, amount):
    """
    Convert an amount from one currency to another.
    
    Endpoint: /conversion/{currency1}/{currency2}/{amount_of_currency1}
    
    Returns the conversion rate and converted amount or appropriate error message.
    """
    # Convert currency codes to uppercase
    currency1 = currency1.upper()
    currency2 = currency2.upper()
    
    # Validate currencies
    if currency1 not in CURRENCY_RATES:
        return JsonResponse(
            {"error": f"Currency '{currency1}' is not supported"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if currency2 not in CURRENCY_RATES:
        return JsonResponse(
            {"error": f"Currency '{currency2}' is not supported"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            return JsonResponse(
                {"error": "Amount must be a positive number"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError:
        return JsonResponse(
            {"error": "Amount must be a valid number"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate conversion rate and converted amount
    # Convert from currency1 to GBP and then to currency2
    rate_to_gbp = 1 / CURRENCY_RATES[currency1]
    gbp_amount = amount * rate_to_gbp
    converted_amount = gbp_amount * CURRENCY_RATES[currency2]
    
    # Calculate direct conversion rate
    conversion_rate = CURRENCY_RATES[currency2] / CURRENCY_RATES[currency1]
    
    # Return the response
    response_data = {
        "from_currency": currency1,
        "to_currency": currency2,
        "amount": amount,
        "conversion_rate": round(conversion_rate, 6),
        "converted_amount": round(converted_amount, 2),
        "supported_currencies": list(CURRENCY_RATES.keys())
    }
    
    return JsonResponse(response_data, status=status.HTTP_200_OK)