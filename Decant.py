from helpers import *

import GEDatabase as db

list_potions = [
    "Saradomin brew",
    "Super restore",
    "Super attack",
    "Super defence",
    "Super strength",
    "Prayer potion",
    "Ranging potion",
    "Super energy",
    #These are so unreliable that they're honestly not worth displaying 99% of the time because they're low-volume
    #"Antidote++"
    #"Super combat potion",
    #"Stamina potion"
    ]

class Decant_Potion:
    name = ''
    buy = 0
    sell = 0
    profit = 0
    roi = 0

    def __init__(self, name):
        self.name = name

def GetPotionDoseList(doses):
    potions = []
    for item in list_potions:
        potions.append(f"{item}({doses})")
    return potions

def SortDecantByRoi(item):
    return item.roi

def BuildPotionsList():
    potion_list = []
    all_doses = []
    for item in db.merged:
        item_name = item['name']
        slice = name.find('(1)')
        if slice >= 0:

            #quick fix for Serum 207 and any other potion that has a space before the dose for some reason
            if name.find(' ('):
                name = name+' '

            potion = {f'{name}':{'id_one_dose':item['id'], 'id_two_dose':None, 'id_three_dose':None, 'id_four_dose':None}}
            potion_list.append(potion)          
    return


def CheckDecantProfits():
    sorted_by_profit = []

    print('DECANTING 3->4  (Profit per 2,000 buylimit):')
    print('*ROIs over 5% are usually not stable for long*\n')

    for potion in list_potions:
        potion_data = Decant_Potion(potion)
        for item in db.merged:
            if item['name'] == potion + "(3)":
                potion_data.buy = item['low']
            if item['name'] == potion + "(4)":
                potion_data.sell = item['high']
        
        buy = potion_data.buy * 2000
        sell = potion_data.sell * 1500
        potion_data.roi = round(CalcRoi(sell, buy), 3)
        profit = round(buy * potion_data.roi /1000, 1)
        potion_data.profit = profit
        if profit > 0:
            sorted_by_profit.append(potion_data)

    sorted_by_profit.sort(reverse=True,key=SortDecantByRoi) #sort from highest to lowest
    for p in sorted_by_profit:
        print(f"{p.name}\n  Profit: {p.profit}K | ROI: {round(p.roi*100,3)}% | 3-dose: {p.buy} | 4-dose: {p.sell}")