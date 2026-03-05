"""
update_scripts.py

Inserts 7 new POIs into data/rio_grande_rift/scripts.json,
then renumbers all POIs sequentially 1–59.

New insertions (using letter suffixes to identify position):
  1b  Franklin Mountains & the El Paso Star         (after old #1)
  3b  The Mission Trail — Three Centuries of Adobe   (after old #3)
  24b San Antonio — The Green Chile Burger           (after old #24)
  26b The Peoples of the Río Grande                  (after old #26)
  27b Coronado's Winter Camp — Bernalillo            (after old #27)
  30b Santa Fe — Palace of the Governors & Canyon Road (after old #30)
  37b Taos Pueblo                                    (after old #37)

Audio file renaming is handled separately by rename_audio.sh.
"""

import json, os

SCRIPTS_PATH = os.path.join(os.path.dirname(__file__),
    "data/rio_grande_rift/scripts.json")

# ---------------------------------------------------------------------------
# New POI definitions
# insert_after: the CURRENT (old) num value after which this POI is inserted
# ---------------------------------------------------------------------------

new_pois = [
    {
        "insert_after": 1,
        "poi": {
            "num": "1b",
            "name": "Franklin Mountains & the El Paso Star",
            "leg": "El Paso",
            "duration": "2:00",
            "words": 296,
            "lat": 31.84,
            "lon": -106.50,
            "cited": True,
            "body": [
                "The mountain range bisecting the city around you is the Franklin Mountains — a 23-mile-long north-south range that runs straight through the middle of El Paso, making it the only major mountain range in the United States entirely contained within a single city. Franklin Mountains State Park protects about 37,000 acres of the range within city limits and is the largest urban wilderness park in the continental United States. [1]",
                "Geologically, the Franklins are the southern tip of the Rocky Mountain chain — the same continental uplift that begins in British Columbia and runs the length of Montana, Colorado, and New Mexico ends here. The rock at the summit is Precambrian granite more than 1.2 billion years old, thrust upward through younger sedimentary layers by faulting along the Rio Grande Rift. The notch you can see cutting through the ridgeline is the Transmountain Road — US-375 — which crosses the range at about 5,300 feet and connects the east side of El Paso to the west. [1]",
                "The large white star on the western flank of the range is the El Paso Star — a 459-foot-wide star made of white-painted rocks laid out by local schoolchildren and community volunteers in 1940. [2] It is illuminated during holidays and for special occasions, visible from the valley floor miles away. For generations of El Paso residents it has been the visual anchor of home — the thing on the mountain that tells you which way you're facing.",
                "The Franklins change color through the day in ways that make them a slow clock for the city below. Red at sunrise, gray by midday, copper and pink in the late afternoon. On the return leg, pay attention to the light on the range as you approach from the north — the granite catches the low angle differently at each hour, and the mountain that looked featureless at noon turns dimensional at dusk."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Franklin Mountains State Park — Texas Parks & Wildlife Department",
                    "url": "https://tpwd.texas.gov/state-parks/franklin-mountains"
                },
                {
                    "n": 2,
                    "text": "El Paso Star: history and dimensions — El Paso Times archive",
                    "url": "https://www.elpasotimes.com/story/news/history/2019/11/11/el-paso-star-history/2558680001/"
                }
            ]
        }
    },
    {
        "insert_after": 3,
        "poi": {
            "num": "3b",
            "name": "The Mission Trail — Three Centuries of Adobe",
            "leg": "El Paso",
            "duration": "2:00",
            "words": 305,
            "lat": 31.74,
            "lon": -106.39,
            "cited": True,
            "body": [
                "You're entering the Mission Trail — and it has a claim worth stating at the start. The three missions along this nine-mile corridor were founded in 1682, making this the oldest mission trail in the United States. The Pilgrims landed at Plymouth in 1620. Jamestown was 1607. The missions on the El Paso Mission Trail predate both the Mayflower and Massachusetts Bay Colony as active communities — and they're still active today. [1]",
                "The trail exists because of catastrophe. The Pueblo Revolt of 1680 drove the entire Spanish colonial population of New Mexico south in a mass retreat — roughly 2,000 colonists and several hundred Pueblo peoples who had aligned with or been brought along by the Spanish fled through the Jornada del Muerto and gathered in the El Paso valley. Among them were Tiwa-speaking people from Isleta Pueblo, Piro people from the Rio Grande villages, and others who would never return north. They established Ysleta, Socorro, and San Elizario along this stretch of the river in the years immediately following the revolt. [2]",
                "What is remarkable about the Mission Trail is not just its age but its continuity. These communities have not been restored or reconstructed — they have been in continuous use. Ysleta Mission has had an active parish since 1682. Socorro Mission has served the same community without interruption for more than three centuries. [3] The people buried in these churchyards are the ancestors of people who live in these communities today. That's not a historical claim. It's a present-tense fact.",
                "The missions are about three miles apart, following the old road south along the river. Ysleta is the first and the oldest. Take your time between them — this stretch of the Rio Grande valley is one of the quietest places on the trip."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Mission Trail, El Paso — El Paso Museum of History",
                    "url": "https://www.epmuseums.org/mission-trail"
                },
                {
                    "n": 2,
                    "text": "Pueblo Revolt 1680: Spanish retreat and mission founding — NPS El Camino Real",
                    "url": "https://www.nps.gov/elca/learn/historyculture/index.htm"
                },
                {
                    "n": 3,
                    "text": "Ysleta del Sur Pueblo and Socorro Mission history — YDSP official",
                    "url": "https://www.ysletadelsurpueblo.org/"
                }
            ]
        }
    },
    {
        "insert_after": 24,
        "poi": {
            "num": "24b",
            "name": "San Antonio — The Green Chile Burger",
            "leg": "El Paso to Albuquerque",
            "duration": "2:00",
            "words": 312,
            "lat": 33.905,
            "lon": -106.87,
            "cited": True,
            "body": [
                "If you didn't stop at the Owl Bar in San Antonio — or if you did and are still thinking about it — here is the full story.",
                "San Antonio, New Mexico, population roughly 160, sits at the northern edge of Bosque del Apache. It has a church, a grain elevator, and two restaurants that have become among the most argued-over food establishments in the Southwest. The Owl Bar & Café has been in operation since 1934. The Buckhorn Tavern opened across the street a few years later. Both serve green chile cheeseburgers. Both claim supremacy. The regulars on each side have strong opinions and are not shy about sharing them.",
                "The Owl Bar's green chile burger became famous in the late 1940s, when workers from the White Sands Missile Range and the Trinity Site — 30 miles east across the Jornada del Muerto — would stop here after long shifts in the restricted desert. The connection is unusual: the most consequential scientific event of the 20th century took place 30 miles from here, and one of the things the workers did afterward was drive to San Antonio and eat a burger with roasted green chile on it. [1] The Buckhorn, for its part, has been declared the best burger in New Mexico by New Mexico Magazine, among others — though the Owl Bar's loyalists dispute the ranking. [2]",
                "The basic formula at both places has not changed in 70 years: a beef patty, green chile roasted on-site, American cheese, a toasted bun. What makes it work is the specificity of the chile — roasted green chile has a smoky, vegetal heat that coats the meat in a way no sauce replicates. You can buy a better burger in most American cities. You cannot buy this one anywhere else."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Owl Bar & Café, San Antonio, NM — New Mexico Magazine",
                    "url": "https://www.newmexicomagazine.org/blog/post/owl-bar-cafe/"
                },
                {
                    "n": 2,
                    "text": "Buckhorn Tavern: best burger in New Mexico — New Mexico Magazine",
                    "url": "https://www.newmexicomagazine.org/blog/post/buckhorn-tavern/"
                }
            ]
        }
    },
    {
        "insert_after": 26,
        "poi": {
            "num": "26b",
            "name": "The Peoples of the Río Grande — A Traveler's Map",
            "leg": "El Paso to Albuquerque",
            "duration": "2:45",
            "words": 418,
            "lat": 34.75,
            "lon": -106.74,
            "cited": True,
            "body": [
                "You've been traveling through the territory of multiple distinct Indigenous nations for several days now. This corridor north of Socorro is a good moment to put the full picture together before you reach Albuquerque and the dense cluster of Pueblo communities to the north.",
                "The Pueblo peoples of the Rio Grande are not a single nation — they're a collection of communities speaking at least five distinct language families. Tiwa is spoken at Taos, Picurís, Sandia, and Isleta, and — as you've seen — by the Tigua at Ysleta del Sur. Tewa is spoken at the six pueblos between Santa Fe and Taos: Ohkay Owingeh, San Ildefonso, Santa Clara, Nambé, Pojoaque, and Tesuque. Towa is spoken only at Jémez Pueblo, west of the Río Grande. And the Keres language is spoken at six pueblos in a wide arc around Albuquerque — Cochiti, Kewa, Zia, Santa Ana, San Felipe, and the more distant Acoma and Laguna. [1] These languages are mutually unintelligible. A Tewa speaker from Santa Clara cannot understand a Keres speaker from Kewa.",
                "What these nations share is a pattern of life: settled, agricultural, organized around village governance and ceremonial life in kivas, with communities that have occupied the same sites — in some cases the same actual buildings — for hundreds of years. The earliest Rio Grande Pueblo sites date to roughly 750 CE; the major pueblos reached their current locations by around 1300 CE. [2]",
                "To the south and east, the Apache nations represent a different cultural tradition entirely: semi-nomadic, organized around extended family bands, historically ranging across vast territories. You've already passed through Mescalero Apache country. The Jicarilla Apache hold land in the mountains to the northwest. To the west, the Diné — the Navajo — are the largest Native nation in the United States by land area, occupying a homeland of roughly 17 million acres in Arizona, New Mexico, and Utah. [3]",
                "These nations have coexisted in this landscape for centuries — trading, sometimes fighting, always negotiating. When you stop at a pueblo, buy from a Native vendor, or walk through a trading post, you are engaging with communities that have maintained their cultural identity through everything this landscape has thrown at them. Pay attention to protocols around photography. Listen when guides explain what is and isn't permitted. The boundaries exist for reasons rooted in long experience."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Pueblo peoples: languages and communities — Pueblo Cultural Center",
                    "url": "https://www.indianpueblo.org/19-pueblos/"
                },
                {
                    "n": 2,
                    "text": "Ancestral Pueblo chronology — Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Puebloans"
                },
                {
                    "n": 3,
                    "text": "Navajo Nation: land area and population — Navajo Nation official",
                    "url": "https://www.navajo-nsn.gov/"
                }
            ]
        }
    },
    {
        "insert_after": 27,
        "poi": {
            "num": "27b",
            "name": "Coronado's Winter Camp — Bernalillo & Kuaua Pueblo",
            "leg": "Albuquerque Area",
            "duration": "2:30",
            "words": 355,
            "lat": 35.30,
            "lon": -106.57,
            "cited": True,
            "body": [
                "Just off the highway in Bernalillo — a few miles north of Albuquerque — is the Coronado Historic Site, which marks one of the stranger episodes in the history of the Southwest: the place where Francisco Vásquez de Coronado wintered in 1540–41, pursuing a geographic fantasy built on a secondhand account told by an enslaved man.",
                "Coronado left Mexico City in February 1540 with 340 Spanish soldiers, 1,300 Mexican Indian allies, and several thousand head of livestock, heading north to find the Seven Cities of Cíbola — the mythical cities of gold that a Franciscan friar named Marcos de Niza claimed to have seen from a distance. Cíbola, when Coronado reached it, turned out to be Háwikuh Pueblo in western New Mexico: a modest stone-and-adobe village whose residents pelted the approaching army with stones. [1] Coronado, furious and wounded, pressed on into the Rio Grande valley. He wintered at Kuaua Pueblo — a large Ancestral Pueblo settlement of around 1,200 rooms on the west bank of the Rio Grande here in Bernalillo.",
                "The encounter was not peaceful. Coronado's forces demanded food and clothing from the surrounding Tiguex pueblos. When the Tiguex people resisted, Coronado's troops besieged the village, burned people at the stake, and conducted a campaign of violence that the Pueblo peoples of the Rio Grande would remember for 140 years — right up to the morning of August 10, 1680, when the Pueblo Revolt began. [2]",
                "Kuaua Pueblo was abandoned before permanent Spanish colonization arrived, but the painted kiva murals recovered during archaeological excavations in the 1930s are originals — geometric, ceremonial, full of birds and rain imagery — and are among the finest examples of pre-contact Pueblo kiva art in existence. [3] They're displayed in the site museum, which is small, free, and genuinely worth the short detour off I-25."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Francisco Vásquez de Coronado expedition — Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Francisco_V%C3%A1squez_de_Coronado"
                },
                {
                    "n": 2,
                    "text": "Tiguex War, 1540–1541 — Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Tiguex_War"
                },
                {
                    "n": 3,
                    "text": "Coronado Historic Site and Kuaua Pueblo murals — New Mexico Historic Sites",
                    "url": "https://www.nmhistoricsites.org/coronado"
                }
            ]
        }
    },
    {
        "insert_after": 30,
        "poi": {
            "num": "30b",
            "name": "Santa Fe — Canyon Road, Indian Market & the Art Capital",
            "leg": "Albuquerque to Santa Fe",
            "duration": "2:30",
            "words": 350,
            "lat": 35.687,
            "lon": -105.938,
            "cited": True,
            "body": [
                "Santa Fe is small — about 85,000 people — and it runs on art, tourism, state government, and a quality of afternoon light that painters have been chasing for a century. It is also, depending on how you measure, between 400 and 500 years older than most American cities.",
                "The Palace of the Governors on the central plaza was built in 1610 and is the oldest public building in continuous use in the United States. [1] The long portal across the front has been used by Native vendors since at least the 19th century, and today is managed as a juried program — artisans from the pueblo and tribal nations of New Mexico hold assigned spaces and sell work made by their own hands. If you're going to buy turquoise or silver anywhere on this trip, buy it here. You are buying directly from the maker, under a program with real standards.",
                "Canyon Road, a 10-minute walk from the plaza, is a mile-long street of galleries, studios, and restaurants that has been the center of Santa Fe's art market since the 1960s. [2] By most counts, Santa Fe has the third-largest art market in the United States after New York and Los Angeles. The galleries range from internationally connected contemporary operations to tourist-grade souvenir shops — the full range is visible on a single walk up the street.",
                "The Indian Market, held every August on the plaza weekend and run by the Southwestern Association for Indian Arts since 1922, is the largest juried Native American art market in the world — around 1,100 artists, up to 150,000 visitors over a single weekend. [3] The work ranges from traditional pottery, weaving, and silverwork to contemporary fine art. The market has a competitive, serious dimension that first-time visitors often don't expect.",
                "Santa Fe's built environment is subject to a design code requiring Pueblo Revival or Territorial style for most new construction — the result of a 1957 ordinance. [4] The adobe walls, the exposed vigas, the earth tones are not an accident. They are a municipal policy, and one that has kept the city looking coherent if occasionally self-conscious."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Palace of the Governors — New Mexico History Museum",
                    "url": "https://www.nmhistorymuseum.org/palace.php"
                },
                {
                    "n": 2,
                    "text": "Canyon Road galleries — Santa Fe Tourism Department",
                    "url": "https://www.santafe.org/santa-fe-arts/canyon-road/"
                },
                {
                    "n": 3,
                    "text": "Indian Market — Southwestern Association for Indian Arts",
                    "url": "https://swaia.org/indian-market/"
                },
                {
                    "n": 4,
                    "text": "Santa Fe historic style ordinance and Pueblo Revival architecture — Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Pueblo_Revival_architecture"
                }
            ]
        }
    },
    {
        "insert_after": 37,
        "poi": {
            "num": "37b",
            "name": "Taos Pueblo",
            "leg": "Santa Fe to Taos",
            "duration": "2:45",
            "words": 414,
            "lat": 36.437,
            "lon": -105.548,
            "cited": True,
            "body": [
                "You're approaching Taos Pueblo — and if this is the only thing you stop for in Taos, that is the right choice.",
                "The two great house complexes of Taos Pueblo — Hlauuma to the north of the creek and Hlaukwima to the south — have been lived in for somewhere between 1,000 and 1,500 years, with archaeological evidence pointing to continuous occupation of the current site since at least 1000 CE. [1] The buildings rise four and five stories in terraced tiers of the same tan adobe as the surrounding high desert. At dusk, with the Sangre de Cristo Mountains going pink behind them, the two house blocks look less like something built than something that grew from the ground.",
                "The Taos people are northern Tiwa speakers — linguistic relatives of the Tigua at Ysleta you visited in El Paso, though separated by geography and centuries of separate history. About 150 residents still live in the old pueblo without electricity or running water in their rooms, by preference. [2] The communal water supply comes from Red Willow Creek, the stream that runs through the middle of the compound, which originates in the mountains above and is itself sacred.",
                "The most important chapter in Taos Pueblo's modern history is the return of Blue Lake. Mä-wha-luu — Blue Lake — is a glacial lake high in the Sangre de Cristo Mountains above the pueblo, the source of Red Willow Creek, and the center of Taos ceremonial life for centuries. In 1906 the U.S. government absorbed the land into the Carson National Forest, and the Taos people were given access as mere visitors to their own sacred ground. [3]",
                "The pueblo spent 64 years fighting for its return. They refused cash settlements, including an offer of $10 million, on the grounds that no amount of money was equivalent to a sacred place. In 1970, Congress passed the Taos Pueblo Blue Lake Bill, returning 48,000 acres including Blue Lake to the pueblo — the first return of land to a Native nation for spiritual reasons in American history. President Nixon signed it as a priority of his Indian policy. [3]",
                "The path from the visitor center to the old pueblo is a five-minute walk. Photography is permitted in common areas but not inside buildings or kivas. The $25 admission goes directly to the pueblo. [4] Take your time."
            ],
            "sources": [
                {
                    "n": 1,
                    "text": "Taos Pueblo: history and archaeology — Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Taos_Pueblo"
                },
                {
                    "n": 2,
                    "text": "Taos Pueblo UNESCO World Heritage Site — UNESCO",
                    "url": "https://whc.unesco.org/en/list/492/"
                },
                {
                    "n": 3,
                    "text": "Blue Lake and the Taos Pueblo Blue Lake Act, 1970 — Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Taos_Pueblo_Blue_Lake"
                },
                {
                    "n": 4,
                    "text": "Taos Pueblo visitor information — Taos Pueblo official",
                    "url": "https://www.taospueblo.com/visit"
                }
            ]
        }
    }
]

# ---------------------------------------------------------------------------
# Load existing scripts
# ---------------------------------------------------------------------------
with open(SCRIPTS_PATH) as f:
    pois = json.load(f)

# Build ordered list: (sort_key, poi_dict)
# We'll use a float sort key so that new POIs can be interleaved
# e.g. insert_after=1 → sort_key 1.5 (between 1 and 2)

ordered = [(float(p["num"]), p) for p in pois]

# Insert new POIs
for entry in new_pois:
    after = entry["insert_after"]
    sort_key = after + 0.5
    ordered.append((sort_key, entry["poi"]))

# Sort by sort_key
ordered.sort(key=lambda x: x[0])

# Renumber sequentially
final = []
for new_num, (_, poi) in enumerate(ordered, start=1):
    poi_copy = dict(poi)
    poi_copy["num"] = new_num
    final.append(poi_copy)

# ---------------------------------------------------------------------------
# Save updated scripts.json
# ---------------------------------------------------------------------------
with open(SCRIPTS_PATH, "w") as f:
    json.dump(final, f, indent=2, ensure_ascii=False)

print(f"Done: {len(final)} POIs written to {SCRIPTS_PATH}")

# ---------------------------------------------------------------------------
# Print the audio renaming mapping for reference
# ---------------------------------------------------------------------------
print("\nAudio file renaming map (old -> new):")
old_nums = [p["num"] for p in pois]  # original numeric sequence
new_assignment = {}
new_idx = 0
for sort_key, poi in sorted(ordered, key=lambda x: x[0]):
    new_idx += 1
    orig_num = poi.get("num")
    if isinstance(orig_num, int) and orig_num in old_nums:
        new_assignment[orig_num] = new_idx

for old, new in sorted(new_assignment.items()):
    if old != new:
        print(f"  {old:02d}.mp3  →  {new:02d}.mp3")
    else:
        print(f"  {old:02d}.mp3  →  {new:02d}.mp3  (unchanged)")
