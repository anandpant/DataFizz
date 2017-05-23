from bs4 import BeautifulSoup
from os import listdir
from os.path import isfile, join
import codecs
import re
from datetime import datetime
import json


class DataProcessing():
    def __init__(self, soup):
        self.soup = soup
    def getTitle(self):
        title = self.soup.find("span", attrs={"id": "btAsinTitle"}).getText()
        return title
    def getAuthor(self):
        value = self.soup.find("span", attrs={"class": "byLinePipe"}).parent.getText()
        author = value.replace(" (Author)", "").replace("\n", "")
        return author
    def getPrice(self):
        try:
            price = self.soup.find("b", attrs={"class": "priceLarge"}).getText()
        except(AttributeError):
            price = self.soup.find("span", attrs={"class": "rentPrice"}).getText()
        return price

    def getWeight(self):
        table = self.soup.find('table', attrs={'id': 'productDetailsTable'})
        table_body = table.find('ul')

        for item in table_body.find_all('li'):
            value = item.getText()
            if "Shipping Weight:" in value:
                weight = re.search('[0123456789.]+', value).group()
                return float(weight)

    def getISBN10(self):
        table = self.soup.find('table', attrs={'id': 'productDetailsTable'})
        table_body = table.find('ul')

        for item in table_body.find_all('li'):
            value = item.getText()
            if "ISBN-10:" in value:
                isbn = value[9:]
                return isbn

class BinPacking():
    def __init__(self, keydict):
        self.keydict = keydict
        self.bins = []
        self.weights = []
    def getPKs(self):
        keylist = list(self.keydict.keys())
        return keylist
    def getBins(self):
        currentbin = []
        for key in self.getPKs():
            if len(currentbin) == 0: #assuming none are too heavy to fit in a single box
                currentbin.append(key)
            else:
                currentsum = 0
                for subkey in currentbin:
                    currentsum += self.keydict[subkey]
                if(currentsum + self.keydict[key] > 10):
                    self.bins.append(currentbin)
                    currentbin = []
                else:
                    currentbin.append(key)
        return self.bins
    def getBinWeight(self):
        for bin in self.bins:
            total = 0
            for item in bin:
                total += self.keydict[item]
            self.weights.append(total)

def parsefile(path):
    with codecs.open("./data/"+path, "r", encoding='utf-8', errors='ignore') as fdata:
        soup = BeautifulSoup(fdata, "lxml")
        return soup

def main():
    now = datetime.now()
    htmllist = [f for f in listdir("./data") if isfile(join("./data", f))]

    keydict = {}
    fulldict = {}
    for item in htmllist:
        dataprocessing = DataProcessing(parsefile(item))

        keydict.update({item:dataprocessing.getWeight()})
        fulldict.update({item:{ "title":dataprocessing.getTitle(), "author":dataprocessing.getAuthor(),
                                "price": dataprocessing.getPrice() + " USD",
                                "shipping_weight": str(dataprocessing.getWeight()) + " pounds",
                                "isbn-10": dataprocessing.getISBN10()}})
    binpacking = BinPacking(keydict)
    binpacking.getBins()
    binpacking.getBinWeight()
    outputdict = {}

    for x in range(0, len(binpacking.bins)):
        contents = []
        for book in binpacking.bins[x]:
            contents.append(fulldict[book])

        outputdict.update({"box"+str(x+1): {"id": x+1, "totalWeight": round(binpacking.weights[x], 1), "contents": contents}})

    with open('./data/output.json', 'w') as fp:
        json.dump(outputdict, fp)
    print(datetime.now()-now)
    
main()