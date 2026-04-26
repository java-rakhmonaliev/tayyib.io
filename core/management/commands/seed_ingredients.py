"""
Management command: python manage.py seed_ingredients
Seeds the database with known halal/haram/questionable ingredients.
Covers: E-codes, common additives, animal derivatives, alcohol-based ingredients.
"""

from django.core.management.base import BaseCommand
from core.models import Ingredient, IngredientStatus

INGREDIENTS = [
    # ── CLEARLY HALAL ────────────────────────────────────────────────────────
    {"name": "water", "status": "halal", "source": "Water is universally halal.", "aliases": ["aqua", "eau"]},
    {"name": "salt", "status": "halal", "source": "Salt is universally halal.", "aliases": ["sodium chloride", "sea salt", "iodized salt"]},
    {"name": "sugar", "status": "halal", "source": "Plant-derived sweetener, halal.", "aliases": ["sucrose", "cane sugar", "beet sugar"]},
    {"name": "glucose", "status": "halal", "source": "Plant-derived sugar.", "aliases": ["dextrose", "corn sugar"]},
    {"name": "fructose", "status": "halal", "source": "Fruit sugar, plant-derived.", "aliases": []},
    {"name": "wheat flour", "status": "halal", "source": "Plant-derived grain product.", "aliases": ["flour", "all-purpose flour", "plain flour", "bread flour"]},
    {"name": "rice", "status": "halal", "source": "Plant-derived grain.", "aliases": ["rice flour", "rice starch"]},
    {"name": "corn starch", "status": "halal", "source": "Plant-derived starch.", "aliases": ["maize starch", "cornstarch"]},
    {"name": "vegetable oil", "status": "halal", "source": "Plant-derived, halal.", "aliases": ["sunflower oil", "canola oil", "rapeseed oil", "palm oil", "soybean oil", "corn oil"]},
    {"name": "olive oil", "status": "halal", "source": "Plant-derived, halal.", "aliases": []},
    {"name": "soy sauce", "status": "halal", "source": "Fermented soy product; trace alcohol from fermentation is generally considered halal by scholars.", "aliases": ["soya sauce"]},
    {"name": "vinegar", "status": "halal", "source": "Acetic acid; transformation (istihalah) makes it halal.", "aliases": ["white vinegar", "apple cider vinegar", "malt vinegar", "balsamic vinegar"]},
    {"name": "yeast", "status": "halal", "source": "Yeast itself is halal; used in bread-making.", "aliases": ["baker's yeast", "dried yeast", "instant yeast"]},
    {"name": "baking soda", "status": "halal", "source": "Mineral compound, halal.", "aliases": ["sodium bicarbonate", "bicarbonate of soda"]},
    {"name": "baking powder", "status": "halal", "source": "Leavening agent, plant/mineral-derived.", "aliases": []},
    {"name": "cocoa", "status": "halal", "source": "Plant-derived, halal.", "aliases": ["cocoa powder", "cacao", "cocoa mass", "cocoa butter"]},
    {"name": "vanilla", "status": "halal", "source": "Plant extract. Pure vanilla extract contains alcohol as carrier — considered halal by majority.", "aliases": ["vanilla extract", "vanilla flavour", "vanillin"]},
    {"name": "citric acid", "status": "halal", "source": "E330. Derived from citrus fermentation, halal.", "aliases": ["e330"]},
    {"name": "ascorbic acid", "status": "halal", "source": "E300. Vitamin C, plant-derived.", "aliases": ["e300", "vitamin c"]},
    {"name": "tocopherol", "status": "halal", "source": "E306-E309. Vitamin E, plant-derived.", "aliases": ["e306", "e307", "e308", "e309", "vitamin e"]},
    {"name": "pectin", "status": "halal", "source": "E440. Plant-derived from citrus/apple, halal.", "aliases": ["e440", "apple pectin", "citrus pectin"]},
    {"name": "carrageenan", "status": "halal", "source": "E407. Derived from seaweed, halal.", "aliases": ["e407", "irish moss extract"]},
    {"name": "agar", "status": "halal", "source": "Derived from seaweed, halal alternative to gelatin.", "aliases": ["agar-agar", "e406"]},
    {"name": "xanthan gum", "status": "halal", "source": "E415. Fermented from corn/soy, halal.", "aliases": ["e415"]},
    {"name": "guar gum", "status": "halal", "source": "E412. Plant-derived from guar beans, halal.", "aliases": ["e412"]},
    {"name": "locust bean gum", "status": "halal", "source": "E410. Plant-derived from carob, halal.", "aliases": ["e410", "carob bean gum"]},
    {"name": "lecithin", "status": "halal", "source": "E322. If from soy or sunflower — halal. If from egg — halal. Source must be verified.", "aliases": ["e322", "soy lecithin", "sunflower lecithin"]},
    {"name": "sodium benzoate", "status": "halal", "source": "E211. Synthetic preservative, halal.", "aliases": ["e211"]},
    {"name": "potassium sorbate", "status": "halal", "source": "E202. Synthetic preservative, halal.", "aliases": ["e202"]},
    {"name": "sorbic acid", "status": "halal", "source": "E200. Synthetic preservative, halal.", "aliases": ["e200"]},
    {"name": "tartaric acid", "status": "halal", "source": "E334. Derived from grapes, halal.", "aliases": ["e334"]},
    {"name": "malic acid", "status": "halal", "source": "E296. Found in fruits, halal.", "aliases": ["e296"]},
    {"name": "lactic acid", "status": "halal", "source": "E270. Fermentation product, halal (if not from pork sources).", "aliases": ["e270"]},
    {"name": "calcium carbonate", "status": "halal", "source": "E170. Mineral, halal.", "aliases": ["e170", "chalk"]},
    {"name": "sodium chloride", "status": "halal", "source": "Salt, halal.", "aliases": []},
    {"name": "caramel colour", "status": "halal", "source": "E150. Derived from sugar, halal.", "aliases": ["e150", "e150a", "e150b", "e150c", "e150d", "caramel color"]},
    {"name": "beta-carotene", "status": "halal", "source": "E160a. Plant/synthetic, halal.", "aliases": ["e160a", "beta carotene"]},
    {"name": "turmeric", "status": "halal", "source": "E100. Spice/natural colour, halal.", "aliases": ["e100", "curcumin"]},
    {"name": "paprika extract", "status": "halal", "source": "E160c. Natural plant colouring, halal.", "aliases": ["e160c", "paprika colour"]},
    {"name": "riboflavin", "status": "halal", "source": "E101. Vitamin B2, halal.", "aliases": ["e101", "vitamin b2"]},
    {"name": "niacin", "status": "halal", "source": "Vitamin B3, halal.", "aliases": ["nicotinic acid", "vitamin b3"]},
    {"name": "inulin", "status": "halal", "source": "Plant-derived prebiotic fibre, halal.", "aliases": ["chicory root extract"]},
    {"name": "maltodextrin", "status": "halal", "source": "Starch-derived, plant-based, halal.", "aliases": []},
    {"name": "modified starch", "status": "halal", "source": "E1400-E1450. Plant-derived starch, halal.", "aliases": ["e1400", "e1404", "e1410", "e1412", "e1420", "e1422", "e1442", "e1450", "modified tapioca starch", "modified corn starch"]},
    {"name": "tapioca starch", "status": "halal", "source": "Plant-derived from cassava, halal.", "aliases": ["tapioca", "cassava starch"]},
    {"name": "potato starch", "status": "halal", "source": "Plant-derived, halal.", "aliases": []},
    {"name": "oat fibre", "status": "halal", "source": "Plant-derived, halal.", "aliases": ["oat bran", "oat flour"]},
    {"name": "acacia gum", "status": "halal", "source": "E414. Plant-derived, halal.", "aliases": ["e414", "gum arabic"]},
    {"name": "cellulose", "status": "halal", "source": "E460. Plant-derived, halal.", "aliases": ["e460", "microcrystalline cellulose", "e461", "e462", "e463", "e464", "e465", "e466"]},
    {"name": "sorbitol", "status": "halal", "source": "E420. Sugar alcohol from fruit, halal.", "aliases": ["e420"]},
    {"name": "mannitol", "status": "halal", "source": "E421. Sugar alcohol, plant-derived, halal.", "aliases": ["e421"]},
    {"name": "xylitol", "status": "halal", "source": "Sugar alcohol from plants, halal.", "aliases": []},
    {"name": "stevia", "status": "halal", "source": "Plant-derived sweetener, halal.", "aliases": ["steviol glycosides", "e960"]},
    {"name": "acesulfame k", "status": "halal", "source": "E950. Synthetic sweetener, halal.", "aliases": ["e950", "acesulfame potassium"]},
    {"name": "aspartame", "status": "halal", "source": "E951. Synthetic sweetener, halal.", "aliases": ["e951"]},
    {"name": "sucralose", "status": "halal", "source": "E955. Derived from sugar, halal.", "aliases": ["e955"]},
    {"name": "saccharin", "status": "halal", "source": "E954. Synthetic sweetener, halal.", "aliases": ["e954"]},
    {"name": "sodium nitrate", "status": "halal", "source": "E251. Curing salt, halal.", "aliases": ["e251"]},
    {"name": "sodium nitrite", "status": "halal", "source": "E250. Preservative, halal.", "aliases": ["e250"]},
    {"name": "sulfur dioxide", "status": "halal", "source": "E220. Preservative, halal.", "aliases": ["e220", "sulphur dioxide"]},
    {"name": "sodium sulfite", "status": "halal", "source": "E221. Preservative, halal.", "aliases": ["e221"]},
    {"name": "calcium chloride", "status": "halal", "source": "E509. Mineral, halal.", "aliases": ["e509"]},
    {"name": "magnesium carbonate", "status": "halal", "source": "E504. Mineral, halal.", "aliases": ["e504"]},
    {"name": "silicon dioxide", "status": "halal", "source": "E551. Anti-caking agent, mineral, halal.", "aliases": ["e551", "silica"]},
    {"name": "titanium dioxide", "status": "halal", "source": "E171. Mineral colouring, halal.", "aliases": ["e171"]},
    {"name": "iron oxide", "status": "halal", "source": "E172. Mineral colouring, halal.", "aliases": ["e172"]},
    {"name": "natural flavouring", "status": "questionable", "source": "Vague term — can include animal-derived components. Source must be verified with manufacturer.", "aliases": ["natural flavor", "natural flavour", "natural flavors"]},
    {"name": "flavouring", "status": "questionable", "source": "Source unknown without manufacturer disclosure. Can be animal or alcohol-derived.", "aliases": ["flavor", "flavour", "artificial flavor", "artificial flavour", "artificial flavouring"]},

    # ── CLEARLY HARAM ────────────────────────────────────────────────────────
    {"name": "pork", "status": "haram", "source": "Quran 2:173, 5:3. Swine is explicitly forbidden.", "aliases": ["pig", "swine", "porcine", "boar"]},
    {"name": "lard", "status": "haram", "source": "Rendered pig fat, explicitly haram.", "aliases": ["pork fat", "pig fat"]},
    {"name": "ham", "status": "haram", "source": "Pork product, haram.", "aliases": []},
    {"name": "bacon", "status": "haram", "source": "Pork product, haram.", "aliases": []},
    {"name": "pork gelatin", "status": "haram", "source": "Derived from pork bones/skin, haram.", "aliases": ["porcine gelatin"]},
    {"name": "blood", "status": "haram", "source": "Quran 2:173. Blood and blood products are haram.", "aliases": ["blood plasma", "dried blood", "porcine blood", "bovine blood"]},
    {"name": "alcohol", "status": "haram", "source": "Intoxicants are haram (Quran 5:90). Ethyl alcohol as a beverage ingredient is haram.", "aliases": ["ethanol", "ethyl alcohol", "spirits"]},
    {"name": "wine", "status": "haram", "source": "Alcoholic beverage, haram.", "aliases": ["red wine", "white wine", "rosé wine"]},
    {"name": "beer", "status": "haram", "source": "Alcoholic beverage, haram.", "aliases": []},
    {"name": "rum", "status": "haram", "source": "Distilled alcohol, haram.", "aliases": []},
    {"name": "whiskey", "status": "haram", "source": "Distilled alcohol, haram.", "aliases": ["whisky", "bourbon", "scotch"]},
    {"name": "vodka", "status": "haram", "source": "Distilled alcohol, haram.", "aliases": []},
    {"name": "brandy", "status": "haram", "source": "Distilled alcohol, haram.", "aliases": []},
    {"name": "liqueur", "status": "haram", "source": "Alcoholic spirit, haram.", "aliases": []},
    {"name": "wine vinegar", "status": "haram", "source": "Scholars disagree; many consider wine vinegar haram as it originates from haram wine intentionally. Plain vinegar (istihalah) is halal.", "aliases": ["red wine vinegar", "white wine vinegar", "sherry vinegar"]},
    {"name": "carmine", "status": "haram", "source": "E120. Derived from cochineal insects. Insects are haram according to most scholars.", "aliases": ["e120", "cochineal", "cochineal extract", "natural red 4", "crimson lake"]},
    {"name": "l-cysteine", "status": "haram", "source": "E920. Often derived from pig or duck feathers or human hair. Seek halal-certified source.", "aliases": ["e920", "cysteine", "l-cystine"]},

    # ── QUESTIONABLE / MADHAB-DEPENDENT ──────────────────────────────────────
    {"name": "gelatin", "status": "questionable", "source": "Source is critical. Pork gelatin = haram. Beef gelatin from non-halal slaughter = haram. Fish/halal-certified beef = halal. Label rarely specifies.", "aliases": ["gelatine", "beef gelatin", "bovine gelatin", "fish gelatin"]},
    {"name": "glycerin", "status": "questionable", "source": "E422. Can be animal-derived (pork/beef) or vegetable-derived. Vegetable glycerin is halal. Source must be confirmed.", "aliases": ["e422", "glycerol", "vegetable glycerin", "vegetable glycerol"]},
    {"name": "mono and diglycerides", "status": "questionable", "source": "E471. Emulsifier — can be derived from animal fats (including pork). Widely debated. Seek halal certification.", "aliases": ["e471", "mono- and diglycerides", "monoglycerides", "diglycerides", "glycerol monostearate"]},
    {"name": "polysorbate 60", "status": "questionable", "source": "E435. Can be derived from animal fats. Source-dependent.", "aliases": ["e435"]},
    {"name": "polysorbate 80", "status": "questionable", "source": "E433. Can be derived from animal fats. Source-dependent.", "aliases": ["e433"]},
    {"name": "polysorbate 20", "status": "questionable", "source": "E432. Can be derived from animal fats. Source-dependent.", "aliases": ["e432"]},
    {"name": "sodium stearoyl lactylate", "status": "questionable", "source": "E481. Emulsifier from stearic acid — can be animal-derived. Source-dependent.", "aliases": ["e481", "ssl"]},
    {"name": "calcium stearoyl lactylate", "status": "questionable", "source": "E482. Like E481 — animal or plant-derived. Source-dependent.", "aliases": ["e482"]},
    {"name": "stearic acid", "status": "questionable", "source": "E570. Can be animal or plant-derived. Source-dependent.", "aliases": ["e570"]},
    {"name": "magnesium stearate", "status": "questionable", "source": "Fatty acid salt — can be animal or plant-derived.", "aliases": []},
    {"name": "rennet", "status": "questionable", "source": "Used in cheese. Animal rennet from non-halal-slaughtered animals = haram. Microbial/vegetable rennet = halal.", "aliases": ["animal rennet", "microbial rennet"]},
    {"name": "cheese", "status": "questionable", "source": "Depends on rennet source. Many cheeses use animal rennet from non-halal slaughter.", "aliases": []},
    {"name": "whey", "status": "questionable", "source": "Cheese by-product — if cheese used non-halal rennet, whey may be haram. Source-dependent.", "aliases": ["whey powder", "whey protein", "whey concentrate"]},
    {"name": "casein", "status": "questionable", "source": "Milk protein — halal if from halal source, but process may involve non-halal enzymes.", "aliases": ["sodium caseinate", "calcium caseinate"]},
    {"name": "shellfish", "status": "hanafi_haram", "source": "Shrimp, crab, lobster etc. Haram according to Hanafi madhab; halal according to Shafi'i.", "aliases": ["shrimp", "prawn", "crab", "lobster", "crayfish", "scallop", "mussel", "oyster", "clam", "squid", "octopus"]},
    {"name": "shark", "status": "hanafi_haram", "source": "Cartilaginous fish — Hanafi consider it makruh/haram; Shafi'i consider it halal.", "aliases": ["shark fin"]},
    {"name": "propylene glycol", "status": "questionable", "source": "E1520. Synthetic solvent. Debated — some scholars consider it halal as it is not intoxicating; others are cautious.", "aliases": ["e1520"]},
    {"name": "isinglass", "status": "questionable", "source": "Fish-derived fining agent used in wine/beer. If in non-alcoholic product, halal. In alcoholic = haram.", "aliases": []},
    {"name": "bone char", "status": "haram", "source": "Used to filter/whiten sugar. Made from animal bones — may be porcine. Seek halal-certified sugar.", "aliases": []},
    {"name": "confectioner's glaze", "status": "questionable", "source": "E904 (Shellac). Derived from lac insect secretions. Insects are haram; this is debated.", "aliases": ["e904", "shellac", "resinous glaze", "lac resin"]},
    {"name": "beeswax", "status": "halal", "source": "E901. From bees — generally considered halal as a coating agent.", "aliases": ["e901"]},
    {"name": "carnauba wax", "status": "halal", "source": "E903. Plant-derived wax, halal.", "aliases": ["e903"]},

    # ── MEAT / SLAUGHTER ─────────────────────────────────────────────────────
    {"name": "beef", "status": "questionable", "source": "Halal only if slaughtered according to Islamic law (zabiha). Conventional beef = haram.", "aliases": ["bovine", "veal"]},
    {"name": "chicken", "status": "questionable", "source": "Halal only if slaughtered Islamically. Conventional chicken = haram.", "aliases": ["poultry", "broiler"]},
    {"name": "lamb", "status": "questionable", "source": "Halal only if slaughtered Islamically.", "aliases": ["mutton", "sheep"]},
    {"name": "meat extract", "status": "questionable", "source": "Source and slaughter method unknown.", "aliases": ["beef extract", "meat broth", "beef broth", "chicken broth", "chicken extract", "bone broth"]},

    # ── ADDITIONAL E-CODES ────────────────────────────────────────────────────
    {"name": "e102", "status": "halal", "source": "Tartrazine. Synthetic yellow dye, halal.", "aliases": ["tartrazine", "fd&c yellow 5"]},
    {"name": "e104", "status": "halal", "source": "Quinoline Yellow. Synthetic dye, halal.", "aliases": ["quinoline yellow"]},
    {"name": "e110", "status": "halal", "source": "Sunset Yellow. Synthetic dye, halal.", "aliases": ["sunset yellow", "fd&c yellow 6"]},
    {"name": "e122", "status": "halal", "source": "Carmoisine. Synthetic red dye, halal.", "aliases": ["carmoisine", "azorubine"]},
    {"name": "e124", "status": "halal", "source": "Ponceau 4R. Synthetic red dye, halal.", "aliases": ["ponceau 4r"]},
    {"name": "e127", "status": "halal", "source": "Erythrosine. Synthetic red dye, halal.", "aliases": ["erythrosine", "fd&c red 3"]},
    {"name": "e129", "status": "halal", "source": "Allura Red. Synthetic red dye, halal.", "aliases": ["allura red", "fd&c red 40"]},
    {"name": "e131", "status": "halal", "source": "Patent Blue V. Synthetic blue dye, halal.", "aliases": ["patent blue v"]},
    {"name": "e132", "status": "halal", "source": "Indigo Carmine. Synthetic blue, halal.", "aliases": ["indigo carmine", "fd&c blue 2"]},
    {"name": "e133", "status": "halal", "source": "Brilliant Blue. Synthetic, halal.", "aliases": ["brilliant blue", "fd&c blue 1"]},
    {"name": "e141", "status": "halal", "source": "Copper complexes of chlorophyll, plant-derived, halal.", "aliases": ["chlorophyll", "e140"]},
    {"name": "e160b", "status": "halal", "source": "Annatto. Natural plant-derived colour, halal.", "aliases": ["e160b", "annatto", "bixin", "norbixin"]},
    {"name": "e160d", "status": "halal", "source": "Lycopene. Natural from tomatoes, halal.", "aliases": ["e160d", "lycopene"]},
    {"name": "e161b", "status": "halal", "source": "Lutein. Natural plant-derived, halal.", "aliases": ["e161b", "lutein"]},
    {"name": "e162", "status": "halal", "source": "Beetroot Red. Natural plant-derived, halal.", "aliases": ["e162", "beetroot red", "betanin"]},
    {"name": "e163", "status": "halal", "source": "Anthocyanins. Natural plant-derived, halal.", "aliases": ["e163", "anthocyanins", "grape skin extract"]},
    {"name": "e210", "status": "halal", "source": "Benzoic Acid. Synthetic preservative, halal.", "aliases": ["e210", "benzoic acid"]},
    {"name": "e212", "status": "halal", "source": "Potassium Benzoate. Synthetic, halal.", "aliases": ["e212"]},
    {"name": "e213", "status": "halal", "source": "Calcium Benzoate. Synthetic, halal.", "aliases": ["e213"]},
    {"name": "e214", "status": "halal", "source": "Ethyl 4-Hydroxybenzoate. Synthetic preservative, halal.", "aliases": ["e214"]},
    {"name": "e280", "status": "halal", "source": "Propionic Acid. Fermentation product, halal.", "aliases": ["e280", "propionic acid"]},
    {"name": "e281", "status": "halal", "source": "Sodium Propionate. Halal.", "aliases": ["e281"]},
    {"name": "e282", "status": "halal", "source": "Calcium Propionate. Halal.", "aliases": ["e282"]},
    {"name": "e316", "status": "halal", "source": "Sodium Erythorbate. Synthetic antioxidant, halal.", "aliases": ["e316"]},
    {"name": "e320", "status": "halal", "source": "BHA. Synthetic antioxidant, halal.", "aliases": ["e320", "bha", "butylated hydroxyanisole"]},
    {"name": "e321", "status": "halal", "source": "BHT. Synthetic antioxidant, halal.", "aliases": ["e321", "bht", "butylated hydroxytoluene"]},
    {"name": "e400", "status": "halal", "source": "Alginic Acid. Seaweed-derived, halal.", "aliases": ["e400", "alginic acid"]},
    {"name": "e401", "status": "halal", "source": "Sodium Alginate. Seaweed-derived, halal.", "aliases": ["e401", "sodium alginate"]},
    {"name": "e402", "status": "halal", "source": "Potassium Alginate. Seaweed-derived, halal.", "aliases": ["e402"]},
    {"name": "e404", "status": "halal", "source": "Calcium Alginate. Seaweed-derived, halal.", "aliases": ["e404"]},
    {"name": "e405", "status": "halal", "source": "Propylene Glycol Alginate. Seaweed base, debated carrier. Generally halal.", "aliases": ["e405"]},
    {"name": "e500", "status": "halal", "source": "Sodium Carbonates. Mineral, halal.", "aliases": ["e500", "sodium carbonate", "sodium bicarbonate"]},
    {"name": "e501", "status": "halal", "source": "Potassium Carbonates. Mineral, halal.", "aliases": ["e501"]},
    {"name": "e503", "status": "halal", "source": "Ammonium Carbonates. Mineral, halal.", "aliases": ["e503"]},
    {"name": "e516", "status": "halal", "source": "Calcium Sulphate. Mineral, halal.", "aliases": ["e516", "calcium sulfate", "gypsum"]},
    {"name": "e901", "status": "halal", "source": "Beeswax. Halal.", "aliases": []},
    {"name": "e950", "status": "halal", "source": "Acesulfame K. Synthetic sweetener, halal.", "aliases": []},
    {"name": "e951", "status": "halal", "source": "Aspartame. Synthetic sweetener, halal.", "aliases": []},
    {"name": "e953", "status": "halal", "source": "Isomalt. Sugar alcohol, plant-derived, halal.", "aliases": ["e953", "isomalt"]},
    {"name": "e955", "status": "halal", "source": "Sucralose. Derived from sugar, halal.", "aliases": []},
    {"name": "e965", "status": "halal", "source": "Maltitol. Sugar alcohol, plant-derived, halal.", "aliases": ["e965", "maltitol"]},
    {"name": "e966", "status": "halal", "source": "Lactitol. Derived from milk lactose, halal.", "aliases": ["e966"]},
    {"name": "e967", "status": "halal", "source": "Xylitol. Plant-derived, halal.", "aliases": ["e967"]},
    {"name": "e968", "status": "halal", "source": "Erythritol. Fermentation product, halal.", "aliases": ["e968", "erythritol"]},
    {"name": "egg", "status": "halal", "source": "Eggs are halal in all madhabs.", "aliases": ["eggs", "whole egg", "egg white", "egg yolk", "dried egg", "egg powder"]},
]


class Command(BaseCommand):
    help = 'Seed the ingredient database'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for item in INGREDIENTS:
            aliases = item.pop('aliases', [])
            obj, was_created = Ingredient.objects.update_or_create(
                name=item['name'],
                defaults={
                    **item,
                    'aliases': aliases,
                    'source_url': item.get('source_url', ''),
                    'notes': item.get('notes', ''),
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created}, Updated: {updated}. Total: {Ingredient.objects.count()} ingredients.'
        ))