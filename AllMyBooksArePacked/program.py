from bs4 import BeautifulSoup
from os import listdir
from os.path import isfile, join
import codecs
import re
import json

#extract parsed info. self explanatory
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

#running sum kept
class Bin(object):
    def __init__(self):
        self.items = []
        self.sum = 0

    def add(self, item): #passed in tuple
        self.items.append(item)
        self.sum += item[1]

    def __dict__(self):
        return str(self.items)


class BinPacking():
    def __init__(self, keydict):
        self.keydict = keydict
        self.bins = []
        self.weights = []

    def getBins(self): #list of objects
        bins = []
        values = sorted(self.keydict.items(), key=lambda x:x[1], reverse=True) #tuples, nlog(n)
        for item in values:
            # Try to fit item into a bin
            for bin in self.bins:
                if bin.sum + item[1] <= 10:
                    bin.add(item)
                    break
            else:
                # item didn't fit into any bin, start a new bin
                bin = Bin()
                bin.add(item)
                self.bins.append(bin)

    def getBinWeight(self):
        for item in self.bins:
            self.weights.append(item.sum)


#convert html to beautifulsoup navigable
def parsefile(path):
    with codecs.open("./data/"+path, "r", encoding='utf-8', errors='ignore') as fdata:
        soup = BeautifulSoup(fdata, "lxml")
        return soup

def main():
    htmllist = [f for f in listdir("./data") if isfile(join("./data", f))]

    keydict = {}
    fulldict = {}
    for item in htmllist:
        dataprocessing = DataProcessing(parsefile(item))

        keydict.update({item:dataprocessing.getWeight()}) #for sorting on weights

        fulldict.update({item:{ "title":dataprocessing.getTitle(), "author":dataprocessing.getAuthor(),
                                "price": dataprocessing.getPrice() + " USD",
                                "shipping_weight": str(dataprocessing.getWeight()) + " pounds",
                                "isbn-10": dataprocessing.getISBN10()}})

    binpacking = BinPacking(keydict)
    binpacking.getBins() # populate self.bins
    binpacking.getBinWeight() # populate self.weights

    #create/populate json file
    outputdict = {}
    x = 0
    for item in binpacking.bins:
        contents = []
        for book in item.items:
            contents.append(fulldict[book[0]])

        outputdict.update({"box"+str(x+1): {"id": x+1, "totalWeight": round(binpacking.weights[x], 1), "contents": contents}})
        x += 1

    with open('output.json', 'w') as fp:
        json.dump(outputdict, fp)

main()