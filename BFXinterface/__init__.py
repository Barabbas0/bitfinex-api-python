'''
Created: 2014-10-22

@author: Andrew Ahern
'''
import calendar
import datetime
import time
import json
import base64
import hashlib
import sys
import hmac
import requests
from decimal import Decimal

class Interface(object):
    '''
    This class acts as an interface for BFX. BFX replies in JSON, this class will convert into Python data structures.
    There's many types of requests, most are very similar. This class aims to be a sort of wrapper, hiding ugly http requests.
    Due to the nature of this class, calls can take seconds at a time.

    Calls are either POSTs or GETs and responses are processed and returned.
    '''
    url = 'https://api.bitfinex.com'
    def getNonce(self):
        '''Nonce must be strictly increasing. Make sure lastNonce is set to 0 in __init__'''
        newNonce = calendar.timegm(datetime.datetime.now().timetuple())
        if newNonce <= int(self.lastNonce): # This seems really hackish. Right now the best alternative seems to be a function that converts to string at the end. - Andrew 2014-10-23
            # print('{0} - newNonce hasn\'t changed. Waiting for new timestamp.'.format(datetime.datetime.now()))
            time.sleep(1)
            newNonce = self.getNonce()
        self.lastNonce = newNonce
        # print('{0} - Returning new nonce: {1}'.format(datetime.datetime.now(), self.lastNonce))
        return str(self.lastNonce)
    def getHTTPheaders(self, payload):
        '''Bitfinex requires very specific headers. This function is to help with obtaining the proper HTTP headers.'''
        jsonPayload = json.dumps(payload)
        payload = base64.b64encode(jsonPayload.encode(encoding='utf_8', errors='strict'))
        signature = hmac.new(self.apiSecret, payload, hashlib.sha384).hexdigest().lower()
        return {'X-BFX-PAYLOAD': payload, 'X-BFX-SIGNATURE': signature, 'X-BFX-APIKEY': self.apiKey}
    def timestampNumberToText(self, timestamp):
        return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    def requestReader(self, response):
        if response.status_code == 200:
            resp = response.json()
            # The next block is to get an actual date back from the method.
            for row in resp:
                if 'timestamp' in row:
                    row['timestamp'] = self.timestampNumberToText(row['timestamp'])
                else:
                    break
            return resp
        elif response.status_code == 400:
            raise NameError('400 Bad Request. Server responded: "{0}"'.format(response.json()['message']))
        else:
            raise NameError('Invalid HTTP code: {0}. Error text: {1}'.format(response.status_code, response.json()['message']))
    def POST(self, requestType, payload=None):
        requestTable = {'balances':'/v1/balances',
                        'newOffer':'/v1/offer/new',
                        'offers':'/v1/offers',
                        'cancelOffer':'/v1/offer/cancel',
                        'balanceHistory': '/v1/history',
                        'dwHistory': '/v1/history/movements',
                        'taken_swaps': '/v1/taken_swaps',
                        'credits': '/v1/credits'}
        url = self.url + requestTable[requestType]
        pl = {'request': requestTable[requestType], 'nonce': self.getNonce()}
        if payload is not None:
            pl = dict(pl, **payload)
        headers = self.getHTTPheaders(pl)
        r = requests.post(url, data=pl, headers=headers, proxies=self.proxies)
        # print('{0} - Requested {1}. HTTP Response: {2}'.format(datetime.datetime.now(), requestTable[requestType], r.status_code))
        return self.requestReader(r)
    def GET(self, requestType, payload=None):
        requestTable = {'lendusd':'/v1/lendbook/USD',
                        'lendbtc':'/v1/lendbook/BTC',
                        'lendltc':'/v1/lendbook/LTC',
                        'orderbookbtcusd':'/v1/book/btcusd',
                        'orderbookbtcltc':'/v1/book/btcltc',
                        'orderbookltcusd':'/v1/book/ltcusd'}
        url = self.url + requestTable[requestType]
        if payload is None:
            payload = {}
        payload.update({'request': requestTable[requestType], 'nonce': self.getNonce()})
        headers = self.getHTTPheaders(payload)
        r = requests.get(url=url, headers=headers, proxies=self.proxies)
        return self.requestReader(r)
    def getBalances(self):
        return self.POST('balances')
    def getLendbook(self, currency):
        payload = {'limit_bids': 256, 'limit_asks': 256}
        response = self.GET('lend{0}'.format(currency), payload)
        print('{0} - Getting {1} lendbook. Bid: {2}% Ask: {3}%'.format(
            datetime.datetime.now(), currency, response['bids'][0]['rate'], response['asks'][0]['rate']))
        return response
    def placeOffer(self, amount, rate, period, currency, direction):
        '''Period must be 2-30. Direction is "lend" or "loan".'''
        payload = {'currency':currency, 'amount':str(amount), 'rate': str(rate),
                   'period':period, 'direction':direction}
        response = self.POST('newOffer', payload)
        return 'Placed {0} offer: {1} for {2} {3} at {4}% for {5} days at {6}.'.format(
            response['direction'],
            response['offer_id'],
            response['original_amount'],
            response['currency'],
            response['rate'],
            response['period'],
            self.timestampNumberToText(response['timestamp']))
    def activeOffers(self):
        return self.POST('offers')
    def cancelOffer(self, offerID):
        payload = {'offer_id': int(offerID)}
        print('{0} - Canceling offer {1}'.format(datetime.datetime.now(), offerID))
        return self.POST('cancelOffer', payload)
    def takenSwaps(self):
        return self.POST('taken_swaps')
    def getCredits (self):
        print('{0} - Getting credits.'.format(datetime.datetime.now()))
        return self.POST('credits')
    def getBalanceHistory(self, currency, since=None, Description=None, until=None, wallet=None):
        '''Takes a currency and optional parameters and returns an array'''
        payload = {'currency': currency}
        if since is not None:
            payload.update({'since': str(since)})
        if until is not None:
            payload.update({'until': str(until)})
        if wallet is not None:
            payload.update({'wallet': wallet})
        resp0 = self.POST('balanceHistory', payload) # resp0 gets converted to resp1
        resp1 = []
        for row in resp0:
            row['balance'] = Decimal(row['balance'])
            row['amount'] = Decimal(row['amount'])
            desc = row['description']
            row['wallet'] = desc.split().pop()
            if desc == 'Swap Payment on wallet deposit':
                desc = 'Interest Earned'
            elif 'Transfer of' in desc:
                desc = desc.split() #Turns desc from a string into a list of strings
                idx = desc.index('to') # 'Transfer of 7.7838 USD from wallet exchange to trading on wallet trading'. Word before "to" is the source wallet, after is destination
                if row['amount'] < 0:
                    desc = 'Transfer from ' + desc[idx-1]
                else:
                    desc = 'Transfer to ' + desc[idx+1]
            elif desc.startswith('Exchange'):
                desc = desc.split()
                idx =  desc.index('for')
                desc = desc[idx-3] + ' ' + desc[idx-2] + ' ' + desc[idx-1]
            elif desc.startswith('Trading fees'):
                desc = 'Trading fees'
            elif desc.startswith('Settlement'):
                desc = 'Settlement'
            elif desc.startswith('Position'):
                desc = desc.split()
                desc = desc[0] + ' ' + desc[2]
            else:
                raise NameError('Error: Couldn\'t read field [\'description\']: {0}'.format(desc))
            if Description is not None:
                if desc != Description:
                    continue
            row['description'] = desc
            resp1.append(row)
        return resp1
    def getDWhistory(self, currency, method=None, since=None, until=None, limit=500):
        payload = { 'currency': currency,
                    'limit': limit}
        if method is not None:
            payload.update({'method': method})
        if since is not None:
            payload.update({'since': self.timestampNumberToText(since)})
        if until is not None:
            payload.update({'until': until})
        return self.POST('dwHistory', payload)
    def getOrderbook(self, symbol, limit_bids=50, limit_asks=50, group=1):
        payload = { 'limit_bids': limit_bids,
                    'limit_asks': limit_asks,
                    'group': group}
        return self.GET('orderbook' + symbol, payload)
    def __init__(self, bfxKey, bfxSecret, proxies=None):
        '''
        bfxKey and bfxSecret are strictly required.
        proxies resembles {'http': 'deer-island:8080', 'https':'deer-island:8080'}
        '''
        print("{0} - Initializing BFXInterface".format(datetime.datetime.now()))

        self.apiKey = bfxKey
        self.apiSecret = bfxSecret
        self.lastNonce = calendar.timegm([1971, 1, 1, 1, 1, 1])
        if proxies is None:
            self.proxies = {}
        else:
            self.proxies = proxies
