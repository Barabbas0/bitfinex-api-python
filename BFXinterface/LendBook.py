'''
LendBook
Created on 2014-10-14
Edited on 2014-10-21 - Class is finished for now. Perhaps next change is support for a nonce object

@author: Andrew Ahern

The purpose of this class is to allow orderly data retrievals from Bitfinex regarding lending.
This class needs to be able to determine whether data obtained is relevant or out of date.
If the data is old, we need to update data, but also want to avoid flooding the server.

fields:
bidArray - An array of bids, identical to askArray. This is irrelevant for now, but remains in case market conditions change.
askArray- Rate (% per 365 days)
        - amount (Decimal)
        - Period (days) - ignored for now
        - timestamp (time) - Useful for gauging market interest
        - frr (yes/no)
        - netAmount - Total Depth for this rate
lastUpdate - used to make sure we're using relevant data
maxAge - The maximum age of the data, in seconds
'''
import datetime
from decimal import Decimal

url = 'https://api.bitfinex.com/v1/lendbook/USD'
maxAge = datetime.timedelta(seconds=15)

class LendBook(object):
    def now(self):
        return datetime.datetime.now()
    def getBidRate(self, depth=0):
        if (self.now() - self.LastUpdate > maxAge):
            self.updateData()
        for row in self.askArray:
            if row['depth'] >= depth:
                return row['rate']
        return self.askArray[-1:]['rate']
    def getAskRate(self, depth=0):
        if (self.now() - self.LastUpdate > maxAge):
            self.updateData()
        response = Decimal()
        for row in self.askArray:
            response = row['rate']
            if row['depth'] >= depth:
                break
        return response
    def updateData(self):
        '''This is the function that updates the internal table based to on the specs above'''
        r = self.BFX.getLendbook(self.currency)
        self.askArray = self.loadArray(rTable=r['asks'])
        self.bidArray = self.loadArray(rTable=r['bids'])
    def loadArray(self, rTable):
        '''This function formats the received JSON into an appropriate python structure'''
        depth = 0
        array = []

        for offer in rTable:
            newRow = {}
            if offer['frr'] == 'Yes':
                newRow['frr'] = True
            else:
                newRow['frr'] = False
            newRow['period'] = int(offer['period'])
            newRow['rate'] = Decimal(offer['rate'])
            newRow['amount'] = Decimal(offer['amount'])
            newRow['timestamp'] = datetime.datetime.fromtimestamp(int(float(offer['timestamp'])))
            depth = depth + Decimal(offer['amount'])
            newRow['depth'] = depth
            array.append(newRow.copy())
        return array
    def __init__(self, BFXcontroller, currency):
        self.askArray = []
        self.bidArray = []
        self.LastUpdate = datetime.datetime.min
        self.BFX = BFXcontroller
        self.currency = currency
        self.updateData()
