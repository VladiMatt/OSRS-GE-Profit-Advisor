#IMPORTS
import requests
import os
import json
from datetime import datetime
import time

null = None #blah
nil = None

db_url = 'https://prices.runescape.wiki/api/v1/osrs/' #base url
headers = {
    'User-Agent': "vladimatts OSRS GE tools",
    'From': 'jmattmurphy1993@gmail.com',
}

map = null
latest = null
lastUpdate = 0
updateCooldown = 30


#DEFS
def Main():
    SelectOption(True)
    wait = input("Press Enter to continue.")

################################################
def SortByProfit(item):
    return item['profit']
def SortByAvgLowPrice(item):
    return item['avgLowPrice']
def SortByAvgHighPrice(item):
    return item['avgHighPrice']
def SortByTimestamp(item):
    return item['timestamp']
def CalcRoi(high, low):
    return((high-(high/100))/low)-1

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
    for item in map:
        if item['name'] == itemname:
            return int(item['id'])
        
def MergeItemDataByID(itemid):
    mergeEntries = ["low", "high"]
    item_map = []
    item_latest = []
    for item in map:
        if item['id'] == itemid:
            item_map = item
            item_latest = latest[str(itemid)]
    
    return {**item_map, **item_latest}

def MergeDatabases():
    item_map = map
    for item in item_map:
        item_latest = {}
        item_latest = GetLatestByID(item['id'])
        if not item_latest:
            item_latest = {'low': 0, 'high': 0, 'highTime':0, 'lowTime':0}
        item_merged = {**item, **item_latest}
        item_map.remove(item)
        item_map.append(item_merged)
    return item_map

def GetLatestByID(id):
    return latest.get(str(id))
    

def LineBreak():
    print("\n################################################\n")
    

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
    print("Done!")
    LineBreak()

################################################
def ReadDatabases():
    global map
    global latest
    global merged
    #not os.path.isfile("ge_map.json") or not os.path.isfile("ge_latest.json") or 
    if (time.time() > lastUpdate+updateCooldown): #pls dont spam their api, only update if the data is older than updateCooldown seconds
        RequestDatabases()
    with open('ge_map.json', 'r') as read_map:
        map = json.load(read_map)
    with open('ge_latest.json', 'r') as read_latest:
        latest = json.load(read_latest)['data']

    merged = MergeDatabases()




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
    #print("These prices were pulled at " + datetime.now().strftime("%H:%M:%S") + "\n")

    for potion in list_potions:
        potion_data = {'name': potion, 'buy': null, 'sell': null, 'profit': null, 'roi': null}
        for item in merged:
            if item['name'] == potion + "(3)":
                potion_data['buy'] = latest[str(item['id'])]['low']
            if item['name'] == potion + "(4)":
                potion_data['sell'] = latest[str(item['id'])]['high']
        
        buy = potion_data['buy'] * 2000
        sell = potion_data['sell'] * 1500
        potion_data['roi'] = CalcRoi(sell, buy)
        profit = round(sell - (sell/100) - buy)
        potion_data['profit'] = profit
        if profit > 0:
            list_profit.append(potion_data)
        else:
           list_loss.append(potion_data)

    list_profit.sort(reverse=True,key=SortByProfit) #sort from highest to lowest
    list_loss.sort(key=SortByProfit)

    print("CURRENT POTENTIAL PROFIT:")
    textFormat = "{potion}: {profit}gp({roi}% ROI) (buy @ {buy}gp, sell @ {sell}gp)"
    for p in list_profit:
        print(textFormat.format(potion = p['name'], profit = p['profit'], buy = p['buy'], sell = p['sell'], roi = round(p['roi']*100, 3)))

    print("\nCURRENT POTENTIAL LOSSES:")
    for p in list_loss:
        print(textFormat.format(potion = p['name'], profit = p['profit'], buy = p['buy'], sell = p['sell'], roi = round(p['roi']*100, 3)))

    

################################################

def CheckDailyMargins():
    marginList = ["Ruby necklace"]
    for item in merged:
        if item['name'] in marginList:
            timeseries_url = "{url}timeseries?timestep={timestep}&id={id}".format(url = db_url, timestep = "5m", id=item['id'])
            timeseries = requests.get(timeseries_url, headers=headers).json()['data']
            timeseries.sort(reverse=True,key=SortByTimestamp)

            #we only want 24 hours worth of data so remove anything older
            #this is REALLY quick and janky but it works for now
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
            text = "{itemname} 24hr low: {low} | 24hr high: {high} | ROI: {roi}%".format(itemname=item['name'],low=dailyLow, high=dailyHigh, roi = CalcRoi(dailyHigh, dailyLow)*100)
            print(text)
            


################################################
Main()