'''
Created: 2014-11-06

Author: Andrew Ahern
'''

from decimal import Decimal
from BFXinterface import LendBook
from datetime import datetime
from datetime import timedelta
import sys

maxLends = {'usd': Decimal(1000.00),
            'btc': Decimal(1.0),
            'ltc': Decimal(100.0)}
exchangeRate = Decimal(1)
class LendingStrategy(object):
    '''
    This class is used as strategy for lending. Arguments can be used to tweak the strategy, as needed.
    '''
    def __init__(self, BFX):
        self.BFX = BFX
        for currency in maxLends:
            balance = min(self.getBalance(currency), maxLends[currency])
            usdBalance = self.checkUSDbalance(balance, currency)
            if usdBalance < Decimal(50.0):
                print('{0} - Not enough {1} balance. Terminating.'.format(datetime.now(), currency))
                continue
            self.cancelAllOffers(currency)
            self.book = LendBook.LendBook(self.BFX, currency)
            ladder = []
            for i in range(2):
                if usdBalance < Decimal(50.0):
                    break
                else:
                    if usdBalance >= Decimal(100):
                        amount = Decimal(50)
                    else:
                        for row in BFX.getCredits():
                            t = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') + timedelta(days=row['period'])
                            n = datetime.now()
                            d = timedelta(minutes=15)
                            if self.checkUSDbalance(Decimal(row['amount']), currency) < Decimal(50) and d > t - n:
                                break
                        amount = usdBalance
                    rate = self.getRate(i)
                    ladder.append({'amount': amount / exchangeRate, 'rate': rate, 'period': self.getPeriod(rate, currency)})
                    usdBalance -= amount
            for row in ladder:
                print('{0} - '.format(datetime.now()) + self.BFX.placeOffer(row['amount'], row['rate'], row['period'], currency, 'lend'))
    def cancelAllOffers(self, currency):
        offers = self.BFX.activeOffers()
        for row in offers:
            if row['currency'] is currency:
                print('{0} - Cancelling offer {1}'.format(datetime.now(), row['id']))
                self.BFX.cancelOffer(int(row['id']))
    def getBalance(self, currency):
        for account in self.BFX.getBalances():
            if account['currency'] == currency and account['type'] == 'deposit':
                balance = Decimal(account['available'])
                print ('{0} - {1} balance: {2}'.format(datetime.now(), currency, balance))
                return balance
        NameError('Deposit {} account not found.'.format(currency))
    def getRate(self, iterNum):
        return (self.book.getAskRate(iterNum * iterNum * Decimal(150000)))
    def getPeriod(self, rate, currency):
        '''This table is for looking up rates. Key is days, value is integer of the annual rate'''
        rateTable ={'usd': {5: 10, 14: 18, 30: 25},
                    'btc': {5: 35, 14: 80, 30: 150},
                    'ltc': {5: 45, 14: 100, 30: 200}}
        period = 2
        for r in rateTable[currency]:
            if rate > rateTable[currency][r]:
                period = max(period, r)
        return period
    def checkUSDbalance(self, balance, currency):
        '''This function assumes minimum of $50 USD'''
        if currency is not 'usd':
            exchangeRate = Decimal(self.BFX.getOrderbook(currency + 'usd')['bids'][0]['price'])
            balance = balance * exchangeRate
        else:
            exchangeRate = 1
        return balance