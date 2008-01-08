from wildcatting.theme.theme import Theme

from wildcatting.welltheory import SimpleWellTheory
from wildcatting.oilprices import GaussianPrices


# we don't want to send _rawFacts into our importers' namespaces
__all__ = ["WestTexas"]

_rawFacts = """
Anadarko will rule the world as we know it. They don't like partners, they now own the UPR strip, much of which is now looking like the biggest gas basins in the US, and they like to drill... and drill... and drill. Everywhere. East Texas Bossier. Cotton Valley. James Lime. Austin Chalk. Just heard of a new hot play? Anadarko probably started it and owns it.
Bud Brigham is a geophysicist who believed in technology. He rode high and he fell hard.  He was hammered for exporing, but now he has SIGNIFICANT wells drilling in Matagorda County and Wheeler County.
Climate scientists are currently neutral as to whether human causes are the the major drivers of Global Warming.
Climate scientists have little faith in their models, the major tool used to "predict" climate change.
The consensus is that climate scientists' models are likely wrong, and there has been little movement from that position in the last decade.
El Paso knocked it out of the park by showing us what the Vicksburg play COULD be in its Tom East Field in Brooks County.
Wells making 60-70 million cubic feet of gas per day can make you healthy real quick.
Like 'em or hate 'em, Aubry McClendon and the folks at Chesapeake believe in the drillbit. They have won big, and lost bigger, but they are still around and kicking... drilling some of the most exciting wells around.
Luis de Moscoso, a survivor of the DeSoto expedition, recorded the first sighting of oil in Texas.
Prices for WTI are quoted at Cushing, Oklahoma, which is a major crude oil shipment point that has extensive pipeline connections to oil producing areas and Southwest and Gulf Coast-based refining centers.
Texas Light Sweet Crude is more formally known as West Texas Intermediate (WTI).
Texas Light Sweet is a type of crude oil used as a benchmark in oil pricing and is the underlying commodity of oil futures contracts.
The Corsicana oilfield developed gradually and peaked in 1900, when it produced more than 839,000 barrels of oil.
The first economically significant discovery of oil in Texas came in 1894 in Navarro County near Corsicana.
The legendary D. Harold (Dry Hole) Byrd was born in Detroit, Texas, on April 24, 1900, the youngest of five sons and three daughters of Edward and Mary (Easley) Byrd.
Thousands of Texans have been touched by Texas' black gold through the philanthropy of people who have made fortunes from its discovery, production and processing.
West Texas Crude is a full-tilt trio from Toowoomba, Queensland who are reviving the traditional rockabilly sounds of the 1950s.  The trio have packed dance floors across Australia with their catchy, high octane rockabilly.
West Texas Intermediate (WTI) is a light crude, lighter than Brent Crude. It contains about 0.24% sulfur, rating it a sweet crude.
The legendary wildcatter Sid Richardson started the family oil business when his mother lent him $40 for train fare to West Texas to "put some deals together."
Perry Richardson Bass became a favorite nephew of his uncle, legendary wildcatter Sid Richardson, and decided to make his living drilling for oil.
Perry Richardson Bass, an avid fisherman, never said goodbye. His parting words were always, 'Tight lines and screaming reels.'"
Perry Richardson Bass called his business a "game," adding, "We'll do anything honest to make a living."
In 1935, Perry Bass, a student at Yale University, and his uncle form Richardson & Bass, an oil venture.  After two dry holes, Richardson hits with the discovery well of the fabulously rich Keystone Field in West Texas' Winkler County.
Sid Williams Richardson was a Texas oilman, cattleman and philanthropist known for his association with the city of Fort Worth.
Sid Williams Richardson was born on 25th April, 1891, in Athens, Texas.
In 1919 Sid Richardson established his own oil company in Fort Worth.  In 1921 the oil market collapsed and he lost most of his fortune.
Sid Richardson had originally been a supporter of the Democratic Party and was associated with a group of right-wing politicians that included Dwight Eisenhower and Lyndon B. Johnson.
Sid Richardson began ranching in the 1930s and developed a love of Western art, particularly that of Frederic Remington and Charles M. Russell. 
Before the big oil companies gained control of the business it was open to any white man who could hustle up the money for a rig, talk a farmer into leasing the mineral rights to his land, and then maintain enough optimism or pigheadedness to drill up his leasehold until he either found oil or convinced himself that he had made a mistake.

# Texas facts
Eighty-five percent of the public libraries in Texas were founded by women's clubs.
Prehistoric tribes in Texas traded for turquoise and obsidian from New Mexico, shell from the Pacific and Atlantic coasts and exotic stone from as far away as Minnesota.
A stone quarry in Texas was used for millennia by inhabitants of the southern Great Plains and is now a monument national Alibates Monument National in the Amarillo area.  
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
Texas is more than an area. Texas is an idea and an experience that transcends present geographical boundaries.
"""


class WestTexas(Theme):
    def __init__(self):
        Theme.__init__(self)
        self._loadFacts(_rawFacts)
        self._wellTheory = SimpleWellTheory(self.getMinOutput(),
                                            self.getMaxOutput())
     
    ## literary setting
    def getLocation(self):
        return "West Texas"
    def getEra(self):
        return "Turn of The Century"

    ## units
    def getDrillIncrement(self):
        return 10
    def getPriceFormat(self):
        return "$%.2f"

    ## extraction
    def getWellTheory(self):
        return self._wellTheory

    ## economics
    def getMinDrillCost(self):
        return 1
    def getMaxDrillCost(self):
        return 25
    def getMinTax(self):
        return 100
    def getMaxTax(self):
        return 550
    def getMinOutput(self):
        return 1
    def getMaxOutput(self):
        return 250
    def newOilPrices(self):
       return GaussianPrices(4.50, 2.0, 5.0)

    ## oil probability distribution
    def getOilMinDropoff(self):
        return 5
    def getOilMaxDropoff(self):
        return 10
    def getOilMaxPeaks(self):
        return 5
    def getOilFudge(self):
        return 4
    def getOilLesserPeakFactor(self):
        return 5

    ## drill cost distribution
    def getDrillCostMinDropoff(self):
        return 5
    def getDrillCostMaxDropoff(self):
        return 6
    def getDrillCostMaxPeaks(self):
        return 10
    def getDrillCostFudge(self):
        return 1
    def getDrillCostLesserPeakFactor(self):
        return 1
