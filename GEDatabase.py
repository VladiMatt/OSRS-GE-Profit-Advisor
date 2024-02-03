import requests
import os
from datetime import datetime
import time


from helpers import *

updateCooldown = 30
lastUpdate = 0
lastUpdateText = ''

db_url = 'https://prices.runescape.wiki/api/v1/osrs/' #base url
headers = {
    'User-Agent': "vladimatts OSRS GE tools",
    'From': 'https://github.com/VladiMatt',
}

merged = None

def GetItemID(itemname):
    for item in merged:
        if item['name'] == itemname:
            return int(item['id'])

def MergeDatabases(item_map, _latest):
    merged_map = []
    for item in item_map:
        item_latest = _latest.get(str(item['id']))

        #some quick and dirty entry fixing to make sure nothing breaks
        if not item_latest:
            item_latest = {'low': 0, 'high': 0, 'highTime':0, 'lowTime':0}
        if item_latest['low'] == None:
            item_latest['low'] = 0
        if item_latest['high'] == None:
            item_latest['high'] = 0
        if item_latest['highTime'] == None:
            item_latest['highTime'] = 0
        if item_latest['lowTime'] == None:
            item_latest['lowTime'] = 0

        item_merged = {**item, **item_latest}
        merged_map.append(item_merged)
    return merged_map
   
################################################
def RequestDatabases():
    global db_url
    global headers
    global merged
    global lastUpdate
    global updateCooldown
    if (time.time() > lastUpdate+updateCooldown): #pls dont spam their api, only update if the data is older than updateCooldown seconds
        print("Fetching new data from prices.runescape.wiki...")

        _map = requests.get(db_url+"mapping", headers=headers).json()
        _latest = requests.get(db_url+"latest", headers=headers).json()['data']

        lastUpdate = round(time.time())
        lastUpdateText = datetime.now().strftime("%H:%M:%S")
        merged = MergeDatabases(_map, _latest)
    LineBreak()