from wildcatting.theme import Theme

raw_facts = """
Anadarko will rule the world as we know it. They don't like partners, they now own the UPR strip, much of which is now looking like the biggest gas basins in the US, and they like to drill... and drill... and drill. Everywhere. East Texas Bossier. Cotton Valley. James Lime. Austin Chalk. Just heard of a new hot play? Anadarko probably started it and owns it.
Bud Brigham is a geophysicist who believed in technology. He rode high and he fell hard.  He was hammered for exporing, but now he has SIGNIFICANT wells drilling in Matagorda County and Wheeler County.
Climate Scientists are currently Neutral as to whether anthropogenic causes are the the major drivers of Global Warming.
Climate Scientists have little faith in their climate models, the major tool used to "predict" climate change and anthropomorphic forcings.  The consensus is that these models are likely wrong, and there has been little movement from that position in the last decade.
El Paso knocked it out of the park by showing us what the Vicksburg play COULD be in its Tom East Field in Brooks Co., Texas! Wells making 60-70 million cubic feet of gas per day can make you healthy real quick.
In 1916, Dr. Johan A. Udden believed there an oil-supporting underground fold of rock running under the University of Texas. Though erroneous, Udden's theory led to the first major oil discovery in the West Texas Permian Basin.
Like 'em or hate 'em, Aubry McClendon and the folks at Chesapeake believe in the drillbit. They have won big, and lost bigger, but they are still around and kicking... drilling some of the most exciting wells around!
Luis de Moscoso, a survivor of the DeSoto expedition, recorded the first sighting of oil in Texas.
Prices for WTI are quoted at Cushing, Oklahoma, which is a major crude oil shipment point that has extensive pipeline connections to oil producing areas and Southwest and Gulf Coast-based refining centers.
Texas Light Sweet Crude is more formally known as West Texas Intermediate (WTI)!
Texas Light Sweet is a type of crude oil used as a benchmark in oil pricing and is the underlying commodity of oil futures contracts.
The Corsicana oilfield developed gradually and peaked in 1900, when it produced more than 839,000 barrels of oil.
The first economically significant discovery of oil in Texas came in 1894 in Navarro County near Corsicana.
The legendary D. Harold (Dry Hole) Byrd was born in Detroit, Texas, on April 24, 1900, the youngest of five sons and three daughters of Edward and Mary (Easley) Byrd.
Thousands of Texans have been touched by Texas' black gold through the philanthropy of people who have made fortunes from its discovery, production and processing.
West Texas Crude is a full-tilt trio from Australia who are reviving the traditional rockabilly sounds of the 1950s.  Formed in the country town of Toowoomba, Queensland, the trio have packed dance floors across Australia with their catchy, high octane rockabilly.
West Texas Intermediate (WTI) is a light crude, lighter than Brent Crude. It contains about 0.24% sulfur, rating it a sweet crude.

# Texas facts
The population of Texas is 21 million, not including the 16 million cattle.
70% of the population of Texas lives within 200 miles of Austin.
Texas possesses three of the Top Ten most populous cities in the U.S. - Houston, Dallas and San Antonio.
Texas' most populous county is Harris county with 3.4 million residents in Houston. The least populated county is Loving county with 67 residents.
Texas has 215 cities with a population of 10,000 or more.
The Dallas-Fort Worth area has more residents - 5,221,801 - than 31 U.S. states. For example, Arizona has about 5.1 million residents.
Texas includes 267,339 square miles, or 7.4% of the nation's total area.
Almost 10% of Texas is covered by forest which includes four national and five state forests.
Texas is popularly known as The Lone Star State.
The lightning whelk is the official state shell of Texas.
More wool comes from the state of Texas than any other state in the United States.
Texas boasts the nation's largest herd of whitetail deer.
Sam Houston, arguably the most famous Texan, was actually born in Virginia.
The Hertzberg Circus Museum in San Antonio contains one of the largest assortments of circusana in the world.
Dr Pepper was invented in Waco in 1885. The Dublin Dr Pepper, 85 miles west of Waco, still uses pure imperial cane sugar in its product. There is no period after the Dr in Dr Pepper.
More species of bats live in Texas than in any other part of the United States.
Amarillo, Texas has the world's largest helium well.
Texas is more than an area. Texas is an idea and an experience that transcends present geographical boundaries!
"""


class WestTexasTheme(Theme):
    ## literary setting
    def getLocation(self):
        return "West Texas"
    def getEra(self):
        return "Turn of The Century"
    def getRawFacts(self):
        return raw_facts

    ## economics
    def getMinDrillCost(self):
        return 1
    def getMaxDrillCost(self):
        return 10
    def getMinTax(self):
        return 100
    def getMaxTax(self):
        return 1000
    def getMaxOutput(self):
        return 16000
    def getInflationAdjustment(self):
        return 0.125

    ## oil probability distribution
    def getOilMinDropoff(self):
        return 5
    def getOilMaxDropoff(self):
        return 20
    def getOilMaxPeaks(self):
        return 5
    def getOilFudge(self):
        return 5
    def getOilLesserPeakFactor(self):
        return 10

    ## drill cost distribution
    def getDrillCostMinDropoff(self):
        return 5
    def getDrillCostMaxDropoff(self):
        return 5
    def getDrillCostMaxPeaks(self):
        return 5
    def getDrillCostFudge(self):
        return 0
    def getDrillCostLesserPeakFactor(self):
        return 10
