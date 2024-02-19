#My code may be ugly


#IMPORTS
import requests
import os
from datetime import datetime
import time


from helpers import *

import Decant
import Flips
import GEDatabase as db




timeseries = None
lastUpdateList = []


def __main__():

    #this is terrible terrible code and I am deeply ashamed of it but it works and that's all that matters
    while(True):
        db.RequestDatabases()
        print("Database timestamp " + db.lastUpdateText)
        print("REMEMBER: These are only ESTIMATES, NOT guaranteed profit!\nThis program automatically subtracts the GE tax")
        LineBreak()
        #Decant.BuildPotionsList()
        Decant.CheckDecantProfits()
        LineBreak()
        #Flips.FindFlips()
        #CheckFlips(None)
        LineBreak()
        print("Speculative high/low prices for pots, based on the past 24 hours of data\n")
        print("3-dose")
        CheckFlips(Decant.GetPotionDoseList(3))
        print("\n4-dose")
        CheckFlips(Decant.GetPotionDoseList(4))
        LineBreak()
        select = input("\nPress ENTER to refresh")
        os.system('cls' if os.name=='nt' else 'clear')
      

################################################


################################################



    
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
    
    def GetDataForDisplay(this): #what the fuck is this? no really, what the fuck?
        data = []
        data.append(this.name)
        data.append(this.dailyLow)
        data.append(this.dailyHigh)
        data.append(this.volumeLow)
        data.append(this.volumeHigh)
        data.append(this.roi)
        data.append(this.limit)
        return data


def CheckFlips(flip_list):
    
    global timeseries
    global lastUpdate
    global lastUpdateList


    #TODO implement better system for saving favorite items
    
    favoritesList = [
                    "Cannonball",
                    "Amylase crystal",
                    #"Weapon poison(++)"
                    ]
    if not flip_list or flip_list == None or flip_list == []:
        flip_list = favoritesList

    #if (time.time() > db.lastUpdate+db.updateCooldown or timeseries == None): #SUPER important to limit api calls here as current implementation makes a call per-item so a large list can result in lots of calls
    if(True):
        lastUpdate = round(time.time())
        lastUpdateList.clear()

        itemlist = []
        
        rate_limit_iteration = 0
        max_api_calls_per_second = 10
        for item in db.merged:
            for flip_list_Item in flip_list:
                if flip_list_Item == item['name']:
                    timeseries_url = "{url}timeseries?timestep={timestep}&id={id}".format(url = db.db_url, timestep = "5m", id=item['id'])
                    timeseries = requests.get(timeseries_url, headers=db.headers).json()['data']

                    #This is a quick and dirty rate limiter to make sure we never hit the API with too many requests
                    rate_limit_iteration += 1
                    if rate_limit_iteration >= max_api_calls_per_second:
                        time.sleep(0.5)
                        #print("Processing...")
                        rate_limit_iteration = 0
                    
                    #we only want 24 hours worth of data so remove anything older
                    #kinda janky but it works for now while we're only working with timesteps of 5 mins
                    minsInADay = 60*24
                    steps = minsInADay/5
                    i = len(timeseries) - steps
                    while i > 0:
                        i-=1
                        timeseries.remove(timeseries[0])
                    
                    timeseries.sort(reverse=True,key=SortByTimestamp)

                    #create the actual item instance
                    flipItem = FlipItem(flip_list_Item)

                    #tally up the low/hgih volumes
                    for data in timeseries:
                        flipItem.volumeLow = flipItem.volumeLow + data['lowPriceVolume'] or 0
                        flipItem.volumeHigh = flipItem.volumeHigh + data['highPriceVolume'] or 0
                    flipItem.volumeLow = round(flipItem.volumeLow/1000,1)
                    flipItem.volumeHigh = round(flipItem.volumeHigh/1000,1)


                    #patch up missing entries so we can sort the list. why do I not just remove them here? I remove them after the list has been sorted, so what even the fuck is this code?
                    for entry in timeseries:
                        if entry['avgLowPrice'] == None:
                            entry['avgLowPrice'] = 0
                        if entry['avgHighPrice'] == None:
                            entry['avgHighPrice'] = 0

                    #determine the thresholds for buy/sell prices
                    #lower thresholds = higher margins but lower volumes
                    buyThreshold = 0.125
                    sellThreshold = 0.05

                    #Determine avg low
                    timeseries.sort(key=SortByAvgLowPrice)
                    while timeseries[0]['avgLowPrice'] == 0 or timeseries[0]['avgLowPrice'] == None:
                        timeseries.remove(timeseries[0]) #clear empty data
                    
                    i = 0
                    while i < round(len(timeseries)*buyThreshold):
                        flipItem.dailyLow = flipItem.dailyLow + timeseries[i]['avgLowPrice']
                        i = i + 1
                    flipItem.dailyLow = round(flipItem.dailyLow / round(len(timeseries)*buyThreshold))
                    
                    timeseries.sort(reverse=True,key=SortByAvgHighPrice)
                    while timeseries[0]['avgHighPrice'] == 0 or timeseries[0]['avgHighPrice'] == None:
                        timeseries.remove(timeseries[0])
                    i = 0
                    while i < round(len(timeseries)*sellThreshold):
                        flipItem.dailyHigh = flipItem.dailyHigh + timeseries[i]['avgHighPrice']
                        i = i + 1
                    flipItem.dailyHigh = round(flipItem.dailyHigh / round(len(timeseries)*sellThreshold))
                    
                    flipItem.roi = round(CalcRoi(flipItem.dailyHigh, flipItem.dailyLow)*100, 3)
                    _margin = flipItem.dailyHigh - flipItem.dailyLow
                    text = f"{flipItem.name}\n  Low: {flipItem.dailyLow} | High: {flipItem.dailyHigh} | ROI: {flipItem.roi}% | Margin: {_margin} | High/Low Volume: {flipItem.volumeHigh}K/{flipItem.volumeLow}K"
                    lastUpdateList.append(text)
                    itemlist.append(flipItem)
    for text in lastUpdateList:
        print(text)
    lastUpdateList.clear()
################################################
        



__main__()