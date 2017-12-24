import sys
import time
import threading

import numpy as np

from   flask import Flask, jsonify, abort, make_response, request
from   flask_httpauth import HTTPBasicAuth

import ccxt

import pymongo
import json



#----------------------------------------------------------------------------
# EXCHANGES SETUP
#----------------------------------------------------------------------------

#\todo Check exchange.hasFetchOHLCV
exchange = ccxt.hitbtc2({'verbose': False})
  
def print_markets():
    hitbtc_markets = exchange.load_markets()
    print(exchange.id, hitbtc_markets)


def fetch_ticker():
    return exchange.fetch_ticker('BTC/USD')


#----------------------------------------------------------------------------
# DATABASE SETUP
#----------------------------------------------------------------------------

def get_datamanager_info(info):
    """Get the 'info' field from the 'datamanager_info' collection at the db.

    It stores parameters that should be kept between runs of the program.

    Args:
        info (str): info field identifier.
            Valid identifiers:
                'fetching_symbols' dict key : PAIR 
                                   dict val : list TIMEFRAME

    Returns:
        Structure stored under 'info'. Can be any data structure.
    """

    try:
        return datamanager_info.find( {info:{'$exists': True}} )[0][info]
    except IndexError:
        datamanager_info.insert_one( {'fetching_symbols':{'BTC/USD':['1m', '3m', '5m',], 'ETH/USD':['1m', '3m', '5m',],} } )
        return datamanager_info.find( {info:{'$exists': True}} )[0][info]



from pkg_resources import resource_filename
datamanager_db_route = resource_filename('orbbit', 'DataManager/datamanager_db.key')

with open(datamanager_db_route) as f:
    datamanager_db_key = json.load(f)    

datamanager_db_connection = pymongo.MongoClient(datamanager_db_key['url'], datamanager_db_key['port'])
datamanager_db = datamanager_db_connection[datamanager_db_key['database']]
datamanager_db.authenticate(datamanager_db_key['user'], datamanager_db_key['password'])

datamanager_info = datamanager_db['datamanager_info']
fetching_symbols = get_datamanager_info('fetching_symbols')



#----------------------------------------------------------------------------
# Generic functions
#----------------------------------------------------------------------------

def timeframe_to_ms(timeframe):
    """ Convert from readable string to milliseconds.
    Args:

        timeframe (str): Valid values:
                             '*m' minutes
                             '*s' seconds
    Returns:
    """
    if 'm' in timeframe:
        return int(timeframe.replace('m', '')) * 60 * 1000
    elif 's' in timeframe:
        return int(timeframe.replace('s', '')) * 1000
    else:
        raise ValueError('Invalid representation.')



#############################################################################
#                        DATAMANAGER TASKS                                  #
#############################################################################

def start_fetch():
    """ Start the fetcher.

    Args:

    Returns:
      List of symbols that are being fetched.

    """
    fetching_symbols = get_datamanager_info('fetching_symbols')
    for symbol in fetching_symbols:
        for timeframe in fetching_symbols[symbol]:
            thread_save_ohlcv = save_ohlcv(symbol, timeframe, time.time()*1000)
            thread_save_ohlcv.start()

    return jsonify({'fetching_symbols': get_datamanager_info('fetching_symbols')})



class save_ohlcv(threading.Thread):
    def __init__(self, symbol, timeframe, curr_time_8061):
        threading.Thread.__init__(self)
        self.symbol = symbol
        self.symbol_db = symbol.replace('/', '_')
        self.timeframe = timeframe
        self.curr_time_8061 = curr_time_8061

    def run(self):
        print('Started fetcher for ' + self.symbol +' '+ self.timeframe)

        collection = datamanager_db[self.symbol_db]
        print(collection)
        nxt_fetch = self.curr_time_8061

        while 1:
            fetch_from_API_success = 0
            while not(fetch_from_API_success):
                try:
                    print('Exchange query for ' + self.symbol +' '+ self.timeframe)
                    ohlcv = exchange.fetch_ohlcv(self.symbol, self.timeframe, nxt_fetch)
                    fetch_from_API_success = 1
                except:
                    time.sleep(1)
        
            if ohlcv:
                new_row = {}
                for candle in ohlcv:
                    new_row['timeframe'] = self.timeframe
                    new_row['date8061']  = candle[0]
                    new_row['open']      = candle[1]
                    new_row['high']      = candle[2]
                    new_row['low']       = candle[3]
                    new_row['close']     = candle[4]
                    new_row['volume']    = candle[5]
                
                    new_document = {'ohlcv':new_row, '_id':(self.timeframe + '_' + candle[0])}

                    print("Fetched OHLCV " + self.symbol + self.timeframe + str(new_row['date8061']))

                    try:
                        collection.insert_one(new_document)
                    except pymongo.errors.DuplicateKeyError as e:
                        print("Duplicate value, skipping.")
                  
                    nxt_fetch += timeframe_to_ms(self.timeframe)
            else:
                time.sleep(10)



def fill_ohlcv(symbol, timeframe, from_millis, to_millis):
    """ Attempt to fill gaps in the DataManager database by fetching many data at once.
        It is limited by how back in time the exchange API provides data.
    
    Args:
        symbol, timeframe, from_millis, to_millis: See save_ohlcv.
    Returns:
        filled: gaps successfully filled.
        missing: gaps that could not be filled.
    """

    # \todo
    return {'filled':filled, 'missing':missing}


#############################################################################
#                          DATAMANAGER API                                  #
#############################################################################

#----------------------------------------------------------------------------
# Flask App error funcs redefinition  
#----------------------------------------------------------------------------

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)



#----------------------------------------------------------------------------
# AUTHENTICATION
#----------------------------------------------------------------------------

auth = HTTPBasicAuth()
""" Add @auth.login_required to a route/method definition to make it 
    password-protected.
"""

@auth.get_password
def get_password(username):
    if username == 'rob':
        return 'bot'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)




#----------------------------------------------------------------------------
# ROUTES AND METHODS
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#   Route /datamanager
#----------------------------------------------------------------------------

@app.route('/datamanager', methods=['GET'])
def datamanager_status():
    """ Get datamanager status.
    Args:

    Returns:
        Status of the DataManager API and processes.
    """

    return jsonify({'fetching_symbols': get_datamanager_info('fetching_symbols')})


#----------------------------------------------------------------------------
#   Route /datamanager/fetch
#----------------------------------------------------------------------------

@app.route('/datamanager/fetch', methods=['GET'])
def fetch():
    return jsonify({'fetching_symbols': get_datamanager_info('fetching_symbols')})


#----------------------------------------------------------------------------
#   Route /datamanager/fetch/<command>
#----------------------------------------------------------------------------

@app.route('/datamanager/fetch/<string:command>', methods=['GET'])
def fetch_commands(command):
    """ Fetcher commands.
    Args:
        start: starts one fetcher per symbol and timeframe as set in fetching_symbols.

        add: add new symbol/timeframe fetcher and start it.

    Returns:
        Symbols/timeframes being fetched.
    """

    # Command <start>
    if command == 'start':
        return start_fetch()


    # Command <add>
    elif command == 'add':
        symbol = request.args.get('symbol').replace('_', '/')
        timeframe = request.json['timeframe']
        fetching_symbols = get_datamanager_info('fetching_symbols')

        if symbol in fetching_symbols:
            if timeframe not in fetching_symbols[symbol]:
                fetching_symbols[symbol].append(timeframe)
                datamanager_info.update_one({'fetching_symbols':{'$exists': True}}, {"$set": {'fetching_symbols':fetching_symbols, } }, upsert=True)
                new_symbol_fetcher = save_ohlcv(symbol, timeframe, time.time()*1000)
                new_symbol_fetcher.start()

        return jsonify({'fetching_symbols': fetching_symbols})

    else:
        return jsonify({'error': 'Invalid command.'})




#----------------------------------------------------------------------------
#   Route /datamanager/get
#----------------------------------------------------------------------------

@app.route('/datamanager/get', methods=['GET'])
def get():
    """ Show DataManager block available data.
    Args:

    Returns:
      
    """

    # \todo List of available data, fetched and processed

    return jsonify({'fetching_symbols': get_datamanager_info('fetching_symbols')})


#----------------------------------------------------------------------------
#   Route /datamanager/get/<command>
#----------------------------------------------------------------------------
@app.route('/datamanager/get/<string:command>', methods=['GET'])
def get_commands(command):
    """ Serve the data collected by the DataManager block.
    Args:

    Returns:
        Requested data.
    """

    # Command <ohlc>
    if command == 'ohlc':
        symbol = request.args.get('symbol').replace('_', '/')
        timeframe = request.json['timeframe']
        from_millis = request.json['from']
        to_millis = request.json['to']

        # \todo
        # busca en db
        # retorna o error

        return jsonify({'fetching_symbols': fetching_symbols})

    else:
        return jsonify({'error': 'Data not available.'})



#----------------------------------------------------------------------------
#   Route /ticker
#----------------------------------------------------------------------------

@app.route('/ticker', methods=['GET'])
def get_ticker():
    """ Get BTC/USD ticker info.

    Args:

    Returns:
      Json-formatted data.
    """

    return jsonify({'ticker': fetch_ticker()})




#----------------------------------------------------------------------------
# PUBLIC METHODS
#----------------------------------------------------------------------------

class DataManager_API (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        print('DataManager_API STARTED with threadID ' + self.name)
        app.run(debug=False)
        print('DataManager_API STOPPED with threadID ' + self.name)


thread_DataManager_API = DataManager_API('thread_DataManager_API')



def start_DataManager_API():
    """ Start DataManager API Server
    Starts in a separate subprocess.

    Args:

    Returns:
      Subprocess ID.
    """

    print("Starting API Server.")
    thread_DataManager_API.start()



#----------------------------------------------------------------------------
# Script-run mode
#----------------------------------------------------------------------------
if __name__ == '__main__':
    print("DataManager Started.")
