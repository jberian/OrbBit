#%% Start spyder (cli)

activate orb_conda

spyder

#%% Start DataManager API
import orbbit as orb
orb.DM.start_API()

#%% Import modules used by these snippets (before sending queries to the API)
import requests 
import ccxt

#%% Get BTC/USD OHLCV 5m
jsonreq = {'symbol':'LTC/USD','timeframe':'1m'}
r = requests.get('http://127.0.0.1:5000/datamanager/get/ohlcv',json=jsonreq)
ohlcv = r.json()
print(len(ohlcv))

#%% export json to file
with open('./save.json', 'w') as f:
    json.dump(ohlcv, f)
    
#%% Add pair
jsonreq = {'symbol':'LTC/USD','timeframe':'1m'}
r = requests.get('http://127.0.0.1:5000/datamanager/fetch/add',json=jsonreq)
print(r.json())

#%% DataManager status
r = requests.get('http://127.0.0.1:5000/datamanager')
print(r.json())

#%% Start fetchers
r = requests.get('http://127.0.0.1:5000/datamanager/fetch/start')
print(r.json())
