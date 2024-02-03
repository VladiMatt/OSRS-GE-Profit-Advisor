import math

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
def SortFlipByRoi(item):
    return item['roi']


#simple line break function to help with separating sections
def LineBreak():
    print(CharLine("-", 100))

def CharLine(character, len):
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