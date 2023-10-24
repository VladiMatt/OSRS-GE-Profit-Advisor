#IMPORTS
import requests
import os
import json
from datetime import datetime
import time
import math

null = None #blah
nil = None

db_url = 'https://prices.runescape.wiki/api/v1/osrs/' #base url
headers = {
    'User-Agent': "vladimatts OSRS GE tools",
    'From': 'jmattmurphy1993@gmail.com',
}

merged = null
lastUpdate = 0
updateCooldown = 30


def Main():
    SelectOption(True)
    wait = input("Press Enter to continue.")

################################################
###### HELPER FUNCTIONS
################################################
def SortByProfit(item):
    return item['profit']
def SortByAvgLowPrice(item):
    return item['avgLowPrice']
def SortByAvgHighPrice(item):
    return item['avgHighPrice']
def SortByTimestamp(item):
    return item['timestamp']
def SortByRoi(item):
    return item['roi']

def LineBreak():
    print("\n################################################\n")

def CalcRoi(high, low):
    return((high-CalcTax(high))/low)-1

def CalcTax(value):
    return math.floor(value/100)

def CalcProfit(investment, roi):
    return investment * roi

################################################
def SelectOption(showHelp):
    commands = ["decant", "margins"]
    if showHelp:
        print("Available commands:")
        for command in commands:
            print(command)
    select = input("\nSelect an option ('help' to view commands): ")
    doShowHelp = False
    match select:
        case "help":
            doShowHelp = True
            select=False
        case "decant":
            select=CheckDecantProfits
        case "margins":
            select=CheckDailyMargins
        case _:
            select=False
            print("UNRECOGNIZED")
    LineBreak()
    if not select == False :
        ReadDatabases() #update the databases if necessary
        select()
    SelectOption(doShowHelp)
    LineBreak()     

################################################
def GetItemID(itemname):
    for item in merged:
        if item['name'] == itemname:
            return int(item['id'])

def MergeDatabases(item_map, latest):
    merged_map = []
    for item in item_map:
        item_latest = latest.get(str(item['id']))

        #some quick and dirty entry fixing to make sure nothing breaks
        if not item_latest:
            item_latest = {'low': 0, 'high': 0, 'highTime':0, 'lowTime':0}
        if item_latest['low'] == null:
            item_latest['low'] = 0
        if item_latest['high'] == null:
            item_latest['high'] = 0
        if item_latest['highTime'] == null:
            item_latest['highTime'] = 0
        if item_latest['lowTime'] == null:
            item_latest['lowTime'] = 0

        item_merged = {**item, **item_latest}
        merged_map.append(item_merged)
    return merged_map
   

    
################################################
def ReadDatabases():
    global merged
    map = null
    latest = null
    if (time.time() > lastUpdate+updateCooldown): #pls dont spam their api, only update if the data is older than updateCooldown seconds
        RequestDatabases()
    with open('ge_map.json', 'r') as read_map:
        map = json.load(read_map)
    with open('ge_latest.json', 'r') as read_latest:
        latest = json.load(read_latest)['data']

    merged = MergeDatabases(map, latest)

################################################
def RequestDatabases():
    global lastUpdate
    global db_url
    global headers
    print("Fetching data from prices.runescape.wiki...")

    _map = requests.get(db_url+"mapping", headers=headers)
    with open('ge_map.json', 'w') as write_map:
        json.dump(_map.json(), write_map)

    _latest = requests.get(db_url+"latest", headers=headers)
    with open('ge_latest.json', 'w') as write_latest:
        json.dump(_latest.json(), write_latest)
    lastUpdate = round(time.time())
    lastUpdateText = datetime.now().strftime("%H:%M:%S")
    print("Database timestamp " + lastUpdateText)
    LineBreak()

################################################

list_potions = [
    "Saradomin brew",
    "Super restore",
    "Super combat potion",
    "Super attack",
    "Super defence",
    "Super strength",
    "Prayer potion",
    "Ranging potion",
    "Stamina potion"
    ]

def CheckDecantProfits():
    list_profit = []
    list_loss = []

    print("Decanting 3->4  profits (per 2000 buy limit)\n")

    for potion in list_potions:
        potion_data = {'name': potion, 'buy': null, 'sell': null, 'profit': null, 'roi': null}
        for item in merged:
            if item['name'] == potion + "(3)":
                potion_data['buy'] = item['low']
            if item['name'] == potion + "(4)":
                potion_data['sell'] = item['high']
        
        buy = potion_data['buy'] * 2000
        sell = potion_data['sell'] * 1500
        potion_data['roi'] = CalcRoi(sell, buy)
        profit = round(CalcProfit(buy, potion_data['roi']))
        potion_data['profit'] = profit
        if profit > 0:
            list_profit.append(potion_data)
        else:
           list_loss.append(potion_data)

    list_profit.sort(reverse=True,key=SortByRoi) #sort from highest to lowest
    list_loss.sort(key=SortByRoi)

    print("CURRENT POTENTIAL PROFIT:")
    textFormat = "{potion}: {profit}gp ({roi}% ROI) (buy @ {buy}gp, sell @ {sell}gp)"
    for p in list_profit:
        print(textFormat.format(potion = p['name'], profit = p['profit'], buy = p['buy'], sell = p['sell'], roi = round(p['roi']*100, 3)))

    print("\nCURRENT POTENTIAL LOSSES:")
    for p in list_loss:
        print(textFormat.format(potion = p['name'], profit = p['profit'], buy = p['buy'], sell = p['sell'], roi = round(p['roi']*100, 3)))

    

################################################

def CheckDailyMargins():
    marginList = [
    {"name":"Ruby necklace", "dailyLow":0, "dailyHigh":0},
    {"name":"Crushed nest", "dailyLow":0, "dailyHigh":0}
    ]
    for item in merged:
        for marginList_Item in marginList:
            if marginList_Item['name'] == item['name']:
                timeseries_url = "{url}timeseries?timestep={timestep}&id={id}".format(url = db_url, timestep = "5m", id=item['id'])
                timeseries = requests.get(timeseries_url, headers=headers).json()['data']
                timeseries.sort(reverse=True,key=SortByTimestamp)

                #we only want 24 hours worth of data so remove anything older
                #kinda janky but it works for now
                minsInADay = 60*24
                steps = minsInADay/5
                i = len(timeseries) - steps
                while i > 0:
                    i-=1
                    timeseries.remove(timeseries[0])

                #patch up missing entries
                for entry in timeseries:
                    if entry['avgLowPrice'] == null:
                        entry['avgLowPrice'] = 0
                    if entry['avgHighPrice'] == null:
                        entry['avgHighPrice'] = 0

                dailyLow = null
                dailyHigh = null
                timeseries.sort(key=SortByAvgLowPrice)
                for entry in timeseries:
                    if entry['avgLowPrice'] > 0 and (not dailyLow or entry['avgLowPrice'] < dailyLow):
                        dailyLow = entry['avgLowPrice']
                timeseries.sort(key=SortByAvgHighPrice)
                for entry in timeseries:
                    if entry['avgHighPrice'] > 0 and (not dailyHigh or entry['avgHighPrice'] > dailyHigh):
                        dailyHigh = entry['avgHighPrice']
                text = "{itemname} 24hr low: {low} | 24hr high: {high} | ROI: {roi}%".format(itemname=item['name'],low=dailyLow, high=dailyHigh, roi=round(CalcRoi(dailyHigh, dailyLow)*100, 3))
                print(text)
            


################################################
Main()