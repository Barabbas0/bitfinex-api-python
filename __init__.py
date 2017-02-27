import base64
import calendar
import csv
import datetime
from decimal import Decimal
import hmac
import json
import time
import sys
import os

import requests

from BFXinterface import Interface
from BFXinterface import LendBook
import LendingStrategy


if __name__ == "__main__":
    apiKey = os.environ.get('BFXKEY')
    apiSecret = os.environ.get('BFXSECRET')

    '''Should use logging or some sort of piping more graceful than simply printing'''
    print('{0} - Program initiated'.format(datetime.datetime.now()))

    BFX = Interface(apiKey, apiSecret)
    LendingStrategy.LendingStrategy(BFX)