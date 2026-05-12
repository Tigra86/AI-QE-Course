import requests
import sys
import json

API_URL = "https://api.frankfurter.app/latest"

def convert_currency(amount, from_currency, to_currency):

    params = {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper()
    }

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if "rates" not in data or to_currency.upper() not in data["rates"]:
        raise ValueError("Invalid currency conversion")

    converted_amount = data["rates"][to_currency.upper()]

    return {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "converted_amount": round(converted_amount, 2)
    }


def main():

    if len(sys.argv) != 4:
        print("Usage:")
        print("python convert_currency.py <amount> <FROM> <TO>")
        print("Example:")
        print("python convert_currency.py 150 EUR USD")
        return

    amount = float(sys.argv[1])
    from_currency = sys.argv[2]
    to_currency = sys.argv[3]

    result = convert_currency(amount, from_currency, to_currency)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
    