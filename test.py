
import json
totalYes = 0
totalNo = 0
buyGame = 0
notBuyGame = 0
    
file = open('calculations.json')
data = json.load(file)

print(data['Purchased'])
print(data['NotPurchased'])





