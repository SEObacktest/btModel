import requests

x=requests.get('https://fapi.binance.com/fapi/v1/time')

print(x.text)