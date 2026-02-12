from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
import json
from payapp.models import CONVERSION_RATES
from decimal import Decimal

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
    if currency1 not in CONVERSION_RATES:
        return JsonResponse(
            {"error": f"Currency '{currency1}' is not supported"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if currency2 not in CONVERSION_RATES:
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
    rate_to_gbp = Decimal('1.0') / CONVERSION_RATES[currency1]
    gbp_amount = Decimal(str(amount)) * rate_to_gbp
    converted_amount = gbp_amount * CONVERSION_RATES[currency2]
    
    # Calculate direct conversion rate
    conversion_rate = CONVERSION_RATES[currency2] / CONVERSION_RATES[currency1]
    
    # Return the response
    response_data = {
        "from_currency": currency1,
        "to_currency": currency2,
        "amount": amount,
        "conversion_rate": round(float(conversion_rate), 6),
        "converted_amount": round(float(converted_amount), 2),
        "supported_currencies": list(CONVERSION_RATES.keys())
    }
    
    return JsonResponse(response_data, status=status.HTTP_200_OK)