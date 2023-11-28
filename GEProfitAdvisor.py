#IMPORTS
import requests
import os
from datetime import datetime
import time
import math

null = None #blah
nil = None

db_url = 'https://prices.runescape.wiki/api/v1/osrs/' #base url
headers = {
    'User-Agent': "vladimatts OSRS GE tools",
    'From': 'https://github.com/VladiMatt',
}

merged = null
lastUpdate = 0
updateCooldown = 30

timeseries = null


def Main():
    #SelectOption(True)
    while(True):
        RequestDatabases()
        print("Database timestamp " + lastUpdateText)
        print("REMEMBER: These are only ESTIMATES, NOT guaranteed profit!\nThis program automatically subtracts the GE tax\n")
        LineBreak()
        CheckDecantProfits()
        LineBreak()
        CheckTrackedMargins()
        LineBreak()
        select = input("\nPress ENTER to refresh")
        os.system('cls' if os.name=='nt' else 'clear')

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

def PrintLine(character, len):
    i = 0
    line = ""
    while i < len:
        i += 1
        line += str(character)
    return line

def CalcRoi(high, low):
    return((high-CalcTax(high))/low)-1

def CalcTax(value):
    return math.floor(value/100)

def DisplayGraph(dataTable):
    print(PrintLine("#", 10))
      

################################################
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
def RequestDatabases():
    global lastUpdate
    global db_url
    global headers
    global lastUpdateText
    global merged
    if (time.time() > lastUpdate+updateCooldown): #pls dont spam their api, only update if the data is older than updateCooldown seconds
        print("Fetching new data from prices.runescape.wiki...")

        _map = requests.get(db_url+"mapping", headers=headers).json()
        _latest = requests.get(db_url+"latest", headers=headers).json()['data']

        lastUpdate = round(time.time())
        lastUpdateText = datetime.now().strftime("%H:%M:%S")
        merged = MergeDatabases(_map, _latest)
    LineBreak()

################################################

list_potions = [
    "Saradomin brew",
    "Super restore",
    "Super attack",
    "Super defence",
    "Super strength",
    "Prayer potion",
    "Ranging potion",
    #These two are so unreliable that they're honestly not worth displaying 99% of the time
     #"Super combat potion",
    #"Stamina potion"
    ]

def CheckDecantProfits():
    sortProfit = []

    print('DECANTING 3->4  (Profit per 2,000 buylimit):')
    print('')
    print('*ROIs over 5% are usually not stable for long*\n')

    for potion in list_potions:
        potion_data = {'name': potion, 'buy': null, 'sell': null, 'profit': null, 'roi': null}
        for item in merged:
            if item['name'] == potion + "(3)":
                potion_data['buy'] = item['low']
            if item['name'] == potion + "(4)":
                potion_data['sell'] = item['high']
        
        buy = potion_data['buy'] * 2000
        sell = potion_data['sell'] * 1500
        potion_data['roi'] = round(CalcRoi(sell, buy), 3)
        profit = round(buy * potion_data['roi'])
        potion_data['profit'] = profit
        if profit > 0:
            sortProfit.append(potion_data)

    sortProfit.sort(reverse=True,key=SortByRoi) #sort from highest to lowest
    for p in sortProfit:
        print(f"{p['name']}\n  Profit: {p['profit']} | ROI: {round(p['roi']*100,3)}% | Low: {p['buy']} | High: {p['sell']}")

    

################################################

class FlipItem:
    name = ""
    dailyLow = 0
    dailyHigh = 0
    volumeLow = 0
    volumeHigh = 0
    roi = 0
    limit = 0

    def __init__(self, name):
        self.name = name


def CheckTrackedMargins():
    global timeseries
    global lastUpdate
    print("SLOW FLIPS (Buy overnight, sell during the day):")
    print("*This feature is still SUPER primitive, so don't expect much!*\n")

    #TODO implement better system for saving favorite items
    
    favoritesList = ["Crushed nest", "Superior dragon bones", "Ruby necklace", "Dark crab"]
    flipItemList = []
    doUpdate = False
    if (time.time() > lastUpdate+updateCooldown or timeseries == null): #SUPER important to limit api calls here as current implementation makes a call per-item so a large list can result in lots of calls
        doUpdate = True
        lastUpdate = round(time.time())
    for item in merged:
        for favoritesList_Item in favoritesList:
            if favoritesList_Item == item['name']:
                timeseries_url = "{url}timeseries?timestep={timestep}&id={id}".format(url = db_url, timestep = "5m", id=item['id'])
                if doUpdate:
                    timeseries = requests.get(timeseries_url, headers=headers).json()['data']
                    
                timeseries.sort(reverse=True,key=SortByTimestamp)

                #create the actual item instance
                flipItem = FlipItem(favoritesList_Item)

                for data in timeseries:
                    flipItem.volumeLow = flipItem.volumeLow + data['lowPriceVolume']
                    flipItem.volumeHigh = flipItem.volumeHigh + data['highPriceVolume']


                #patch up missing entries so we can sort the list
                for entry in timeseries:
                    if entry['avgLowPrice'] == null:
                        entry['avgLowPrice'] = 0
                    if entry['avgHighPrice'] == null:
                        entry['avgHighPrice'] = 0

                #determine the averages... lower sensitivity = higher margins but lower volumes
                avgSensitivity = 0.05
                avgRange = round(len(timeseries)*avgSensitivity)

                #Determine avg low
                timeseries.sort(key=SortByAvgLowPrice)
                while timeseries[0]['avgLowPrice'] == 0 or timeseries[0]['avgLowPrice'] == null:
                    timeseries.remove(timeseries[0]) #clear empty data
                
                i = 0
                while i < avgRange:
                    flipItem.dailyLow = flipItem.dailyLow + timeseries[i]['avgLowPrice']
                    i = i + 1
                flipItem.dailyLow = round(flipItem.dailyLow / avgRange)
                
                timeseries.sort(reverse=True,key=SortByAvgHighPrice)
                while timeseries[0]['avgHighPrice'] == 0 or timeseries[0]['avgHighPrice'] == null:
                    timeseries.remove(timeseries[0])
                i = 0
                while i < avgRange:
                    flipItem.dailyHigh = flipItem.dailyHigh + timeseries[i]['avgHighPrice']
                    i = i + 1
                flipItem.dailyHigh = round(flipItem.dailyHigh / avgRange)
                
                flipItem.roi = round(CalcRoi(flipItem.dailyHigh, flipItem.dailyLow)*100, 3)
                _margin = flipItem.dailyHigh - flipItem.dailyLow
                text = f"{flipItem.name}\n  Low: {flipItem.dailyLow} | High: {flipItem.dailyHigh} | ROI: {flipItem.roi}% | Margin: {_margin} | High/Low Volume: {flipItem.volumeHigh}/{flipItem.volumeLow}"
                print(text)
                flipItem = null #clear the flipItem just in case...?

    flipItemList.clear()
            


################################################
Main()