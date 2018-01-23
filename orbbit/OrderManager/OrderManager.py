#!/usr/bin/python3

import sys
import time
import threading
import queue
import numpy as np
import socket
from   flask      import Flask, jsonify, abort, make_response, request
from   flask_cors import CORS
import asyncio
import ccxt.async as ccxt
import pymongo
import json

from   orbbit.common.common import *



#%%##########################################################################
#                               CONFIGURATION                               #
#############################################################################

#%%--------------------------------------------------------------------------
# NETWORK
#----------------------------------------------------------------------------

# API
ORDERMANAGER_API_IP = '0.0.0.0'
ORDERMANAGER_API_PORT = 5001




#%%##########################################################################
#                              DATABASE SETUP                               #
#############################################################################




#%%##########################################################################
#                              EXCHANGES SETUP                              #
#############################################################################

user_info = get_database_info('ordermanager', 'user_info')

user_exchanges = {}
for user in user_info:
    user_exchanges[user] = {exchange: exchange_id_to_user_exchange(exchange, user) for exchange in user_info[user]['exchanges']}




#%%##########################################################################
#                              ORDERMANAGER API                              #
#############################################################################

#----------------------------------------------------------------------------
# Flask app error funcs redefinition
#----------------------------------------------------------------------------

ordermanager_flask_app = Flask(__name__)
CORS(ordermanager_flask_app)

@ordermanager_flask_app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'URL not found'}), 404)

@ordermanager_flask_app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)



#----------------------------------------------------------------------------
# ROUTES AND METHODS
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#   Route /ordermanager
#----------------------------------------------------------------------------

@ordermanager_flask_app.route('/ordermanager', methods=['POST'])
def ordermanager_status():
    """ Get ordermanager status.
    Args:

    Returns:
        Status of the OrderManager API and processes.
    """

    return jsonify({'status': 'aaaaa'})



#----------------------------------------------------------------------------
#   Route /ordermanager/get
#----------------------------------------------------------------------------

@ordermanager_flask_app.route('/ordermanager/get', methods=['POST'])
def get():
    """ List ordermanager available data.

    Trhough 'get', you can retrieve sets of past data stored in the database.
    To receive the latest data see '/ordermanager/subscribe'

    Args:

    Returns:
      Available OHLCV symbols and timeframes.
    """

    # \todo List of available data, fetched and processed

    # print('RECEIVED REQ /ordermanager/get')
    # print(request.json)

    return jsonify({'balance': {'STRAT': 4.57623799, 'BTC': 4e-08, 'QTUM': 2.0, 'OMG': 9.05145261, 'EMC2': 104.84758895, 'WAVES': 10.48232595, 'PTOY': 151.82511483, 'ETH': 0.03701968, 'USDT': 0.00286782}})



#----------------------------------------------------------------------------
#   Route /ordermanager/get/<command>
#----------------------------------------------------------------------------

@ordermanager_flask_app.route('/ordermanager/get/', methods=['POST'])
def get_commands():
    """ Serve data collected by the OrderManager block.

    Args:

    Returns:
        trade_history (dict)
            symbol
            amount
            price

    Example:
        get_resource = 'trade_history'
        get_parameters = {'user': 'farolillo', 'exchange': 'hitbtc2'}

        get_resource = 'trade_history'
        get_parameters = {'user': 'linternita', 'exchange': 'bittrex'}

        get_resource = 'balance'
        get_parameters = {'user': 'linternita', 'exchange': 'bittrex'}

        get_resource = 'balance_usd'
        get_parameters = {'user': 'farolillo', 'exchange': 'hitbtc2'}

    """
    # print('RECEIVED REQ /ordermanager/get/')
    # print(request.json)

    get_resource = request.json['res']
    get_parameters = request.json['params']


    # Resource 'balance'
    if get_resource == 'balance':
        user        = get_parameters['user']
        exchange_id = get_parameters['exchange']

        balance = get_balance(user_exchanges[user][exchange_id])

        return jsonify({'balance': balance})


    # Resource 'balance_usd'
    if get_resource == 'balance_usd':
        user        = get_parameters['user']
        exchange_id = get_parameters['exchange']

        balance_usd, total_usd = get_balance_usd(user_exchanges[user][exchange_id])

        return jsonify({'balance_usd': balance_usd, 'total_usd': total_usd})


    # Resource 'trade_history'
    elif get_resource == 'trade_history':
        user        = get_parameters['user']
        exchange_id = get_parameters['exchange']

        if 'symbol' in get_parameters:
            symbol = get_parameters['symbol']
        else:
            symbol = None


        trade_history = get_trade_history(user_exchanges[user][exchange_id], symbol)

        return jsonify({'trade_history': trade_history})


    # Resource 'balance_norm_price_history'
    elif get_resource == 'balance_norm_price_history':
        user        = get_parameters['user']
        exchange_id = get_parameters['exchange']
        timeframe   = get_parameters['timeframe']

        balance_norm_price_history = get_balance_norm_price_history(user_exchanges[user][exchange_id], timeframe)

        return jsonify({'balance_norm_price_history': balance_norm_price_history})       


    # Resource 'open_orders'
    elif get_resource == 'open_orders':
        user        = get_parameters['user']
        exchange_id = get_parameters['exchange']

        open_orders = get_open_orders(user_exchanges[user][exchange_id])

        return jsonify({'open_orders': open_orders})

    else:
        return jsonify({'error': 'Resource not found.'})




#%%--------------------------------------------------------------------------
# PUBLIC METHODS
#----------------------------------------------------------------------------

class ordermanager_API (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        print('OrderManager API STARTED with threadID ' + self.name)
        ordermanager_flask_app.run(host=ORDERMANAGER_API_IP, port=ORDERMANAGER_API_PORT, debug=False)
        print('OrderManager API STOPPED with threadID ' + self.name)


thread_ordermanager_API = ordermanager_API('thread_ordermanager_API')


def start_API():
    """ Start OrderManager API Server
    Starts in a separate subprocess.

    Args:

    Returns:
    """
    print("Starting OrderManager API Server.")
    thread_ordermanager_API.start()


#----------------------------------------------------------------------------
# Script mode
#----------------------------------------------------------------------------
if __name__ == '__main__':
    print("OrderManager in script mode.")
    start_API()
