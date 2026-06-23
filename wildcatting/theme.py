import abc
import logging

from wildcatting.model import Setting
from wildcatting.oilprices import OilPrices, TrendingGaussianPrices
from wildcatting.welltheory import SimpleWellTheory


class Theme(abc.ABC):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        self._facts: list[str] = []

    def _load_facts(self, raw_facts: str) -> None:
        facts = []
        for line in raw_facts.split("\n"):
            fact = line.strip()
            if fact == "":
                continue

            if fact[0] == "#":
                continue

            facts.append(fact)

        self._facts = facts

    def generate_setting(self) -> Setting:
        setting = Setting()
        setting.location = self.get_location()
        setting.era = self.get_era()
        setting.price_format = self.get_price_format()
        setting.facts = self.facts
        setting.min_drill_cost = self.get_min_drill_cost()
        setting.max_drill_cost = self.get_max_drill_cost()
        setting.drill_increment = self.get_drill_increment()
        return setting

    @property
    def facts(self) -> list[str]:
        return self._facts

    ## literary setting
    @abc.abstractmethod
    def get_location(self) -> str: ...

    @abc.abstractmethod
    def get_era(self) -> str: ...

    # units
    @abc.abstractmethod
    def get_drill_increment(self) -> int: ...

    @abc.abstractmethod
    def get_price_format(self) -> str: ...

    ## extraction
    @abc.abstractmethod
    def get_well_theory(self) -> SimpleWellTheory: ...

    @abc.abstractmethod
    def get_mean_site_reserves(self) -> int: ...

    ## economics
    @abc.abstractmethod
    def get_min_drill_cost(self) -> int: ...

    @abc.abstractmethod
    def get_max_drill_cost(self) -> int: ...

    @abc.abstractmethod
    def get_min_tax(self) -> int: ...

    @abc.abstractmethod
    def get_max_tax(self) -> int: ...

    @abc.abstractmethod
    def get_min_output(self) -> int: ...

    @abc.abstractmethod
    def get_max_output(self) -> int: ...

    @abc.abstractmethod
    def get_oil_prices(self) -> OilPrices: ...

    ## oil probability distribution
    @abc.abstractmethod
    def get_oil_max_peaks(self) -> int: ...

    @abc.abstractmethod
    def get_oil_fudge(self) -> int: ...

    @abc.abstractmethod
    def get_oil_lesser_peak_factor(self) -> int: ...

    ## drill cost distribution
    @abc.abstractmethod
    def get_drill_cost_max_peaks(self) -> int: ...

    @abc.abstractmethod
    def get_drill_cost_fudge(self) -> int: ...

    @abc.abstractmethod
    def get_drill_cost_lesser_peak_factor(self) -> int: ...


# we don't want to send _raw_facts into our importers' namespaces
__all__ = ["Theme", "WestTexas", "DefaultTheme"]

_raw_facts = """
Anadarko will rule the world as we know it. They don't like partners, they now own the UPR strip, much of which is now looking like the biggest gas basins in the US, and they like to drill.
Everywhere. East Texas Bossier. Cotton Valley. James Lime. Austin Chalk. Just heard of a new hot play? Anadarko probably started it and owns it.
Bud Brigham is a geophysicist who believed in technology. He rode high and he fell hard.
Bud Brigham was hammered for exporing, but now he has SIGNIFICANT wells drilling in Matagorda County and Wheeler County.
Climate scientists are currently neutral as to whether human causes are the the major drivers of Global Warming.
Climate scientists have little faith in their models, the major tool used to "predict" climate change.
The consensus is that climate scientists' models are likely wrong, and there has been little movement from that position in the last decade.
El Paso knocked it out of the park by showing us what the Vicksburg play COULD be in its Tom East Field in Brooks County.
Wells making 60-70 million cubic feet of gas per day can make you healthy real quick.
Like 'em or hate 'em, Aubry McClendon and the folks at Chesapeake believe in the drillbit. They have won big, and lost bigger, but they are still around and kicking... drilling some of the most exciting wells around.
Luis de Moscoso, a survivor of the DeSoto expedition, recorded the first sighting of oil in Texas.
Prices for WTI are quoted at Cushing, Oklahoma, which is a major crude oil shipment point.
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
Perry Richardson Bass, an avid fisherman, never said goodbye. His parting words were always, 'Tight lines and screaming reels.'
Perry Richardson Bass called his business a "game," adding, "We\'ll do anything honest to make a living."
In 1935, Perry Bass, a student at Yale University, and his uncle form Richardson & Bass, an oil venture.  After two dry holes, Richardson hits with the discovery well of the fabulously rich Keystone Field in West Texas\' Winkler County.
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
    def __init__(self) -> None:
        Theme.__init__(self)
        self._load_facts(_raw_facts)
        self._wellTheory = SimpleWellTheory(self.get_max_output())
        self._prices = TrendingGaussianPrices(4.50, 1.0, 25.0, 8.0, 5.0)

    ## literary setting
    def get_location(self) -> str:
        return "West Texas"

    def get_era(self) -> str:
        return "Turn of The Century"

    ## units
    def get_drill_increment(self) -> int:
        return 10

    def get_price_format(self) -> str:
        return "$%.2f"

    ## extraction
    def get_well_theory(self) -> SimpleWellTheory:
        return self._wellTheory

    def get_mean_site_reserves(self) -> int:
        return 666

    def get_min_output(self) -> int:
        return 1

    def get_max_output(self) -> int:
        return 66

    ## economics
    def get_min_drill_cost(self) -> int:
        return 1

    def get_max_drill_cost(self) -> int:
        return 25

    def get_min_tax(self) -> int:
        return 100

    def get_max_tax(self) -> int:
        return 550

    def get_oil_prices(self) -> TrendingGaussianPrices:
        return self._prices

    ## oil probability distribution
    def get_oil_max_peaks(self) -> int:
        return 5

    def get_oil_fudge(self) -> int:
        return 4

    def get_oil_lesser_peak_factor(self) -> int:
        return 5

    ## drill cost distribution
    def get_drill_cost_max_peaks(self) -> int:
        return 10

    def get_drill_cost_fudge(self) -> int:
        return 1

    def get_drill_cost_lesser_peak_factor(self) -> int:
        return 1


DefaultTheme = WestTexas
