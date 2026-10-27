"""Static, fictional seed tables for Bayline Courier."""

SEED_NUMBER = 20260912
BUSINESS_KEY = "bayline"
OWNER_NAME = "Rosa Delgado"
TAGLINE = "Price every job from the van that already drives past."

DEPOT = {"name": "Emeryville depot", "address": "Powell St, Emeryville", "lat": 37.8395, "lon": -122.2920}
SOMA_LOT = {"name": "SoMa lot", "address": "Harrison St, San Francisco", "lat": 37.7785, "lon": -122.4056}

AREAS = {
    "Downtown Berkeley": (37.8703, -122.2680),
    "Elmwood": (37.8580, -122.2530),
    "North Berkeley": (37.8895, -122.2830),
    "West Berkeley": (37.8690, -122.2990),
    "Emeryville": (37.8395, -122.2920),
    "Temescal": (37.8370, -122.2620),
    "Rockridge": (37.8440, -122.2510),
    "Piedmont Ave and Pill Hill": (37.8225, -122.2600),
    "Lakeshore": (37.8115, -122.2475),
    "Downtown Oakland": (37.8044, -122.2712),
    "Courthouse area": (37.7990, -122.2650),
    "Jack London": (37.7955, -122.2780),
    "SF Financial District": (37.7929, -122.4030),
    "Embarcadero": (37.7955, -122.3937),
    "SoMa": (37.7810, -122.4000),
    "Mission Bay": (37.7680, -122.3920),
    "Mission": (37.7590, -122.4150),
}

# Waterfront areas: stops east of this longitude would sit in the bay, so they are mirrored back inland.
SHORELINE_LON = {"Embarcadero": -122.3945, "SF Financial District": -122.3965, "Mission Bay": -122.3905, "SoMa": -122.3925}


AREA_SHORT = {
    "Downtown Berkeley": "Berkeley", "Elmwood": "Elmwood", "North Berkeley": "North Berkeley",
    "West Berkeley": "West Berkeley", "Emeryville": "Emeryville", "Temescal": "Temescal",
    "Rockridge": "Rockridge", "Piedmont Ave and Pill Hill": "Pill Hill", "Lakeshore": "Lakeshore",
    "Downtown Oakland": "Uptown", "Courthouse area": "Lakeside", "Jack London": "Jack London",
    "SF Financial District": "Financial District", "Embarcadero": "Embarcadero", "SoMa": "SoMa",
    "Mission Bay": "Mission Bay", "Mission": "Mission",
}

STREETS = {
    "Downtown Berkeley": ("Berkeley", [("Shattuck Ave", 2000, 2300), ("University Ave", 1900, 2200), ("Center St", 2000, 2200), ("Milvia St", 1900, 2200), ("Allston Way", 1900, 2200), ("Addison St", 2000, 2200), ("Oxford St", 2000, 2200)]),
    "Elmwood": ("Berkeley", [("College Ave", 2700, 2990), ("Ashby Ave", 2500, 2800), ("Russell St", 2600, 2900), ("Benvenue Ave", 2800, 3000), ("Webster St", 2700, 2900)]),
    "North Berkeley": ("Berkeley", [("Shattuck Ave", 1400, 1700), ("Vine St", 1400, 1600), ("Cedar St", 1400, 1700), ("Walnut St", 1400, 1600), ("Hopkins St", 1500, 1800), ("Henry St", 1300, 1500)]),
    "West Berkeley": ("Berkeley", [("4th St", 1700, 2000), ("San Pablo Ave", 1800, 2400), ("Gilman St", 800, 1200), ("Parker St", 700, 1000), ("Heinz Ave", 700, 900), ("Ashby Ave", 700, 1000)]),
    "Emeryville": ("Emeryville", [("Powell St", 1200, 1600), ("Hollis St", 5800, 6400), ("Horton St", 5800, 6200), ("Park Ave", 1200, 1500), ("40th St", 1200, 1500), ("Bay St", 5600, 5800), ("Christie Ave", 5800, 6200)]),
    "Temescal": ("Oakland", [("Telegraph Ave", 4600, 5100), ("40th St", 400, 700), ("51st St", 400, 600), ("Claremont Ave", 5000, 5300), ("Racine St", 4900, 5200), ("Clarke St", 4800, 5000)]),
    "Rockridge": ("Oakland", [("College Ave", 5300, 5790), ("Claremont Ave", 5600, 6000), ("Miles Ave", 5800, 6100), ("Lawton Ave", 5400, 5600), ("Keith Ave", 5500, 5800)]),
    "Piedmont Ave and Pill Hill": ("Oakland", [("Piedmont Ave", 3500, 3890), ("Webster St", 3000, 3300), ("Summit St", 3000, 3300), ("MacArthur Blvd", 200, 500), ("Howe St", 3700, 4100), ("30th St", 300, 500)]),
    "Lakeshore": ("Oakland", [("Lakeshore Ave", 3100, 3290), ("Grand Ave", 3200, 3500), ("Mandana Blvd", 800, 1000), ("Walavista Ave", 700, 900), ("Trestle Glen Rd", 700, 900)]),
    "Downtown Oakland": ("Oakland", [("Franklin St", 1200, 1700), ("Webster St", 1300, 1700), ("Clay St", 1400, 1600), ("Telegraph Ave", 1600, 2000), ("14th St", 300, 600), ("Harrison St", 1300, 1700), ("Jefferson St", 1200, 1500)]),
    "Courthouse area": ("Oakland", [("Fallon St", 1100, 1300), ("Oak St", 1100, 1300), ("Madison St", 1100, 1300), ("13th St", 100, 300), ("Lakeside Dr", 1300, 1600), ("2nd Ave", 1100, 1300)]),
    "Jack London": ("Oakland", [("Water St", 50, 200), ("2nd St", 200, 500), ("3rd St", 400, 700), ("Alice St", 200, 400), ("Webster St", 300, 500), ("Washington St", 300, 500)]),
    "SF Financial District": ("San Francisco", [("Montgomery St", 100, 290), ("California St", 300, 600), ("Sansome St", 100, 500), ("Battery St", 100, 500), ("Pine St", 200, 500), ("Bush St", 100, 400), ("Kearny St", 100, 400)]),
    "Embarcadero": ("San Francisco", [("Steuart St", 1, 200), ("Spear St", 1, 300), ("Main St", 1, 300), ("Beale St", 1, 300), ("Drumm St", 1, 200), ("Davis St", 1, 400)]),
    "SoMa": ("San Francisco", [("Folsom St", 500, 1000), ("Howard St", 500, 1000), ("Harrison St", 500, 900), ("Bryant St", 400, 800), ("2nd St", 300, 700), ("4th St", 300, 700), ("Townsend St", 400, 800)]),
    "Mission Bay": ("San Francisco", [("Owens St", 1500, 1800), ("4th St", 1500, 1900), ("Berry St", 500, 800), ("Channel St", 100, 300), ("Illinois St", 600, 900), ("16th St", 400, 700)]),
    "Mission": ("San Francisco", [("Mission St", 2000, 2900), ("Valencia St", 500, 1200), ("24th St", 2500, 3200), ("Guerrero St", 500, 1000), ("18th St", 3200, 3600)]),
}

AREA_TYPES = {
    "Downtown Berkeley": ["Law office", "Law office", "Print shop", "Pharmacy", "Medical office", "Florist"],
    "Elmwood": ["Dental office", "Pharmacy", "Florist", "Medical office"],
    "North Berkeley": ["Dental office", "Pharmacy", "Florist", "Medical office"],
    "West Berkeley": ["Lab", "Lab", "Print shop", "Florist"],
    "Emeryville": ["Lab", "Lab", "Lab", "Print shop"],
    "Temescal": ["Medical office", "Dental office", "Pharmacy", "Print shop"],
    "Rockridge": ["Dental office", "Medical office", "Medical office", "Florist", "Pharmacy"],
    "Piedmont Ave and Pill Hill": ["Medical office", "Medical office", "Dental office", "Lab", "Pharmacy"],
    "Lakeshore": ["Dental office", "Medical office", "Florist", "Pharmacy"],
    "Downtown Oakland": ["Law office", "Law office", "Law office", "Print shop"],
    "Courthouse area": ["Law office", "Law office", "Print shop"],
    "Jack London": ["Law office", "Print shop", "Florist"],
    "SF Financial District": ["Law office", "Law office", "Law office", "Print shop"],
    "Embarcadero": ["Law office", "Print shop", "Florist"],
    "SoMa": ["Print shop", "Law office", "Pharmacy", "Lab"],
    "Mission Bay": ["Lab", "Lab", "Lab", "Medical office", "Pharmacy"],
    "Mission": ["Pharmacy", "Florist", "Print shop", "Dental office"],
}

TEMPLATES = {
    "Lab": ["{w} Bio", "{w} Genomics", "{w} Diagnostics", "{w} Biosciences", "{w} Therapeutics", "{w} Clinical Lab"],
    "Law office": ["{s} & {s2} LLP", "{s} Law Group", "{s} Legal", "{s} {s2} Attorneys"],
    "Dental office": ["{a} Family Dental", "{s} Dental", "{a} Smile Studio", "{s} Orthodontics"],
    "Medical office": ["{a} Internal Medicine", "{s} Pediatrics", "{a} Cardiology", "{a} Dermatology", "{a} Orthopedics", "{s} Family Practice"],
    "Print shop": ["{st} Print & Copy", "{w} Printworks", "{w} Copy Center"],
    "Pharmacy": ["{a} Pharmacy", "{s} Apothecary", "{st} Drugs"],
    "Florist": ["{w} Florals", "{s} Flowers", "{a} Blooms"],
    "Clinic": ["{a} Urgent Care", "{a} Community Clinic", "{s} Health Clinic"],
    "Architect": ["{s} Architects", "{w} Design Studio", "{s} {s2} Architecture"],
    "Engineering office": ["{w} Engineering", "{s} Structural"],
    "Copy shop": ["{st} Copy & Ship", "{w} Copies"],
    "Auto parts": ["{a} Auto Parts", "{w} Auto Supply"],
}

WORDS = ["Bayside", "Helix", "Northgate", "Cobalt", "Sequoia", "Harbor", "Meridian", "Tidewater", "Alder",
         "Pinnacle", "Quarry", "Redwood", "Juniper", "Lumen", "Strata", "Keystone", "Wharf", "Foundry",
         "Clearwater", "Granite", "Summit", "Larkspur", "Ironbark", "Pacifica", "Sterling", "Marigold",
         "Tamarack", "Beacon", "Copperleaf", "Driftwood"]
SURNAMES = ["Whitaker", "Nguyen", "Castillo", "Brennan", "Okoro", "Lindqvist", "Harper", "Moreno", "Tanaka",
            "Fischer", "Oduya", "Bellamy", "Rosen", "Kaur", "Delacroix", "Ibarra", "Sato", "Mercer",
            "Halvorsen", "Abernathy", "Quintero", "Feld", "Lowell", "Prescott", "Vance", "Tran", "Esposito",
            "Kowalski", "Duarte", "Ashford", "Galloway", "Pruitt", "Yamamoto", "Barros", "Ellison"]

# Prospect categories from spec section 9 with OSM tags and typical hours (minutes since midnight).
PROSPECT_CATEGORIES = [
    ("Dental office", "amenity=dentist", 480, 1020),
    ("Medical office", "amenity=doctors", 480, 1020),
    ("Clinic", "amenity=clinic", 480, 1140),
    ("Pharmacy", "amenity=pharmacy", 540, 1260),
    ("Lab", "healthcare=laboratory", 420, 1080),
    ("Law office", "office=lawyer", 540, 1080),
    ("Architect", "office=architect", 540, 1080),
    ("Copy shop", "shop=copyshop", 480, 1140),
    ("Print shop", "craft=printer", 540, 1080),
    ("Florist", "shop=florist", 540, 1080),
    ("Auto parts", "shop=car_parts", 480, 1140),
    ("Engineering office", "office=engineer", 540, 1080),
]

# Fixed stops that the demo flows depend on.
VAN2_SHATTUCK = {
    "customer_name": "Shattuck Avenue Imaging", "customer_type": "Medical office",
    "address": "5100 Shattuck Ave, Oakland", "street": "Shattuck Ave", "city": "Oakland",
    "lat": 37.8355, "lon": -122.2641, "kind": "pickup", "service_minutes": 3, "price_per_visit": 12.0,
    "area": "Temescal",
}
VAN2_TELEGRAPH = {
    "customer_name": "Ashby Pediatrics", "customer_type": "Medical office",
    "address": "3000 Telegraph Ave, Berkeley", "street": "Telegraph Ave", "city": "Berkeley",
    "lat": 37.8551, "lon": -122.2598, "kind": "pickup", "service_minutes": 4, "price_per_visit": 11.5,
    "area": "Temescal",
}
def seg(area, count, at):
    return {"type": "area", "area": area, "count": count, "at": at}


def fixed(stop, at):
    return {"type": "fixed", "stop": stop, "at": at}


# Segment anchor times are minutes since midnight. target_spare tunes the final segment.
# Each van drives one geographic loop: every area once, in driving order, no back-and-forth.
VANS = [
    {"key": "van-1", "name": "Van 1", "nickname": "Shattuck loop", "driver": "Maria Alvarez",
     "phone": "(510) 555-0101", "color": "#60A5FA", "base": "depot", "target_spare": 45,
     "segments": [seg("North Berkeley", 7, 510), seg("Downtown Berkeley", 7, 660), seg("Elmwood", 6, 820)]},
    {"key": "van-2", "name": "Van 2", "nickname": "Emeryville labs", "driver": "Dev Patel",
     "phone": "(510) 555-0102", "color": "#A78BFA", "base": "depot", "target_spare": 50,
     "segments": [seg("Emeryville", 7, 500), seg("Temescal", 6, 660), fixed(VAN2_SHATTUCK, 830),
                  fixed(VAN2_TELEGRAPH, 855), seg("West Berkeley", 5, 900)]},
    {"key": "van-3", "name": "Van 3", "nickname": "Oakland legal", "driver": "Sam Okafor",
     "phone": "(510) 555-0103", "color": "#F472B6", "base": "depot", "target_spare": 40,
     "segments": [seg("Downtown Oakland", 7, 510), seg("Courthouse area", 6, 690), seg("Jack London", 7, 840)]},
]

DIRECTORY = [
    ("Temescal Diagnostics Lab", "5200 Shattuck Ave, Oakland", 37.8372, -122.2642, "Medical lab", 480, 1080, "8am to 6pm", "(510) 555-0141"),
    ("Ashby Medical Center", "Ashby Ave and Telegraph Ave, Berkeley", 37.8557, -122.2591, "Hospital", 0, 1440, "Open 24 hours", "(510) 555-0150"),
    ("Lakeshore Dental", "3300 Lakeshore Ave, Oakland", 37.8121, -122.2446, "Dental office", 480, 990, "8am to 4:30pm", "(510) 555-0163"),
    ("Piedmont Ave Lab", "4000 Piedmont Ave, Oakland", 37.8268, -122.2546, "Medical lab", 420, 1140, "7am to 7pm", "(510) 555-0164"),
    ("Clay Street Law Group", "1300 Clay St, Oakland", 37.8034, -122.2752, "Law office", 480, 1080, "8am to 6pm", "(510) 555-0142"),
    ("Fallon Street Courthouse", "Fallon St and 12th St, Oakland", 37.7985, -122.2647, "Courthouse", 480, 960, "8am to 4pm", "(510) 555-0170"),
    ("Third Street Print", "600 3rd St, San Francisco", 37.7800, -122.3940, "Print shop", 540, 1080, "9am to 6pm", "(415) 555-0143"),
    ("Montgomery Partners", "300 Montgomery St, San Francisco", 37.7920, -122.4025, "Office", 480, 1080, "8am to 6pm", "(415) 555-0171"),
    ("Rockridge Florist", "5800 College Ave, Oakland", 37.8460, -122.2520, "Florist", 540, 1080, "9am to 6pm", "(510) 555-0119"),
    ("Elmwood Pharmacy", "2900 College Ave, Berkeley", 37.8585, -122.2530, "Pharmacy", 540, 1140, "9am to 7pm", "(510) 555-0172"),
    ("Emeryville Central Lab", "1400 Powell St, Emeryville", 37.8388, -122.2905, "Medical lab", 420, 1200, "7am to 8pm", "(510) 555-0173"),
]

REQ1_TEXT = ("Hi! We need a daily pickup at our lab on Shattuck around 2, dropping specimens at Ashby Medical Center. "
             "Weekdays starting next week. What would that cost? Thanks, Rina, Temescal Diagnostics, 5200 Shattuck")

# (number, source, sender, sender_contact, received minutes, text, what it tests)
REQ11_TEXT = """---------- Forwarded message ---------
From: Purchasing <po@lakeshoredental.example>
Date: Fri, Oct 23
Subject: PO 4471 courier service
To: Bayline Courier <dispatch@baylinecourier.example>

Please see the PO below and set this up.

PURCHASE ORDER 4471
Vendor: Bayline Courier
Service: Courier pickup and delivery
Pickup: Lakeshore Dental
Deliver to: Piedmont Ave Lab
Schedule: Weekdays starting next week, pickup at 3pm
Approved by: Dana Ortiz, Office Manager"""

REQ12_TEXT = """Re: Re: Re: holiday party + courier

Sounds good, see everyone Friday!

--
Jules Park | Office Coordinator | Montgomery Partners
300 Montgomery St, San Francisco

On Thu, Oct 22, Sam Lee wrote:
> Jules, can you also sort out the courier thing? We need a one-off pickup tomorrow at 10am from Third Street Print (600 3rd St) for the signed contracts, delivered to us at Montgomery Partners by 11am.
>
> On Wed, Oct 21, Jules Park wrote:
>> Catering is booked for the whole floor. Parking is on 2nd St.
>> Thanks, Jules"""

REQ13_TEXT = """[10/23, 4:02 PM] Maya (Elmwood Pharmacy): hey! quick q
[10/23, 4:02 PM] Maya (Elmwood Pharmacy): can your van grab a prescription bag from us
[10/23, 4:03 PM] Maya (Elmwood Pharmacy): and bring it to Ashby Medical Center
[10/23, 4:03 PM] Bayline Dispatch: sure, when?
[10/23, 4:05 PM] Maya (Elmwood Pharmacy): today around 1 if possible
[10/23, 4:05 PM] Maya (Elmwood Pharmacy): thx!!"""

REQ14_TEXT = """Hi Bayline,

Two separate things this week:
1) Tomorrow at 9am, pick up a centerpiece order at Rockridge Florist and deliver it to Lakeshore Dental.
2) Every Friday starting next week, pick up at Rockridge Florist at 2pm and take the arrangements to Ashby Medical Center.

Thanks, Tom"""

REQUESTS = [
    (1, "email", "Rina at Temescal Diagnostics Lab", "rina@temescaldiagnostics.example", 485, REQ1_TEXT, "The main demo. Van 2 should win."),
    (2, "text", "Clay Street Law Group", "(510) 555-0142", 500, "can u do a same day run from 1300 clay st to the courthouse on fallon by 3? 2 boxes", "A one-off job with a pickup and a dropoff"),
    (3, "email", "Third Street Print", "orders@thirdstreetprint.example", 512, "We need pickups Mondays and Thursdays at 11 from our shop at 600 3rd St, delivering to Montgomery Partners at 300 Montgomery.", "Specific weekdays"),
    (4, "text", "Lakeshore Dental", "(510) 555-0163", 523, "need pickup at 5pm today at lakeshore dental to piedmont ave lab", "Handling a mistake, because the office closes at 4:30"),
    (5, "pdf", "Eastside Clinic Group", "rfq@eastsideclinics.example", 531, "Request for quote. Daily courier service for 4 clinics. Pickups between 3:00 and 4:00pm at 4100 Piedmont Ave, 5600 College Ave, 3100 Telegraph Ave and 2900 College Ave. Deliver to Emeryville Central Lab, 1400 Powell St, by 5:00pm.", "Several stops in one request"),
    (6, "voicemail", "Tom at Rockridge Florist", "(510) 555-0119", 544, "Hi, this is Tom from Rockridge Florist on College. We need deliveries Friday afternoons to about five homes in Montclair. Call me back.", "Missing addresses, so it needs a question"),
    (7, "text", "Unknown sender", "(415) 555-0177", 552, "pickup 1450 broadway tomorrow 10am deliver to mission st", "An ambiguous city and address"),
    (8, "email", "Northside Books", "hello@northsidebooks.example", 560, "Pick up at 8:00am at 2000 University Ave Berkeley and deliver to Mission Bay by 8:15am please.", "An impossible window"),
    (9, "email", "Rina at Temescal Diagnostics Lab", "rina@temescaldiagnostics.example", 490, REQ1_TEXT, "Duplicate detection"),
    (10, "photo", "Photo of a handwritten note", "(510) 555-0178", 570, "Daily 11:30 pickup Elmwood Pharmacy. 2 drops on Solano Ave.", "Reading a photo"),
    (11, "email", "Lakeshore Dental purchasing", "po@lakeshoredental.example", 575, REQ11_TEXT, "A forwarded purchase order"),
    (12, "email", "Jules at Montgomery Partners", "office@montgomerypartners.example", 582, REQ12_TEXT, "A long reply chain, real ask mid-thread"),
    (13, "text", "Maya at Elmwood Pharmacy", "(510) 555-0191", 588, REQ13_TEXT, "A pasted WhatsApp chat"),
    (14, "email", "Tom at Rockridge Florist", "tom@rockridgeflorist.example", 594, REQ14_TEXT, "One email with two separate jobs"),
]

DISPATCH_PROMPTS = [
    "Which van has the most spare time today?",
    "Why is Van 2's next stop where it is?",
    "Never send Van 1 to SF after 3pm.",
]
UNIT_PROMPTS = DISPATCH_PROMPTS
