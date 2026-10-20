#!/usr/bin/env python3
"""Generate synthetic, industry-realistic SAP snapshots for the industry / customer selector.

    python3 scripts/generate_tenants.py      -> data/tenants/*.json + data/tenants/index.json

Deterministic (seeded per customer). Every company, person, e-mail (reserved .example domain) and phone number is fictional;
locations, product families and supply-chain patterns are realistic for the industry. The original cosmetics demo
(Aurelia Cosmetics, data/sap_mock.json) is kept as-is and registered as the default tenant.
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tenants"
AS_OF = date(2026, 10, 20)
ZONE = {"FR": "Europe", "DE": "Europe", "IT": "Europe", "ES": "Europe", "BE": "Europe", "NL": "Europe", "PL": "Europe", "CZ": "Europe", "IE": "Europe",
        "CH": "Europe", "SE": "Europe", "GB": "Europe", "AE": "Middle East", "SG": "Asia-Pacific", "KR": "Asia-Pacific", "CN": "Asia-Pacific",
        "IN": "Asia-Pacific", "MY": "Asia-Pacific", "JP": "Asia-Pacific", "VN": "Asia-Pacific", "US": "North America", "MX": "North America",
        "CA": "North America", "CL": "South America", "BR": "South America", "AU": "Asia-Pacific", "CI": "Africa", "GH": "Africa", "MA": "Africa"}
FIRST = ["Anna", "Lukas", "Marta", "Pierre", "Sofia", "Daniel", "Elena", "Tomas", "Yuki", "Ravi", "Chloé", "Jonas", "Priya", "Marco", "Lena", "Omar", "Mei", "Carlos", "Nadia", "Felix"]
LAST = ["Keller", "Novak", "Rossi", "Lambert", "Andersen", "Moreau", "Schmidt", "Tanaka", "Sharma", "Costa", "Weber", "Haddad", "Chen", "Silva", "Kowalski", "Martens"]

# ---------------------------------------------------------------------------------------------------------- specs
# plants: (code, name, type, country, city, lat, lon)
# fgs: (code, description, uom, unit_cost, safety, {dc: daily demand}, cover_days {dc: days}, plant, [(component, qty per unit, scrap %)])
# components: (code, description, type, uom, unit_cost, safety)
# suppliers: (name, country, city, lat, lon, site, [materials], lead_days, otif_target, secondary, price, freight, order_qty, profile)
# quotes: (supplier, material, price, freight, order_qty, lead, qualified, country, city, lat, lon)
# origins: (ingredient, origin, country, lat, lon, feeds_supplier, feeds_material, share %, transit, variability, criticality, note)
SPECS = {
    ("cosmetics", "lumiere"): {
        "company": "Lumière Beauty Group", "domain": "lumiere-demo.example", "prefix": "LB",
        "plants": [("FR30", "Orléans Haircare Factory", "factory", "FR", "Orléans", 47.90, 1.91), ("PL10", "Kraków Colour Cosmetics Plant", "factory", "PL", "Kraków", 50.06, 19.94),
                   ("DC31", "Frankfurt EU Hub", "warehouse", "DE", "Frankfurt", 50.05, 8.57), ("DC32", "Newark US DC", "warehouse", "US", "Newark", 40.72, -74.17),
                   ("DC33", "Shanghai China DC", "warehouse", "CN", "Shanghai", 31.23, 121.47)],
        "fgs": [("FG-SHAMPOO-400", "Repair Shampoo 400 ml", "EA", 3.9, 2500, {"DC31": 650, "DC32": 520, "DC33": 300}, {"DC31": 18, "DC32": 4, "DC33": 22}, "FR30",
                 [("RM-SURFACTANT", 0.12, 2), ("RM-KERATIN", 0.004, 3), ("PK-HDPE-400", 1, 1.5), ("PK-CAP-FLIP", 1, 1)]),
                ("FG-LIPSTICK-RUBY", "Velvet Lipstick Ruby", "EA", 2.6, 1500, {"DC31": 300, "DC32": 260, "DC33": 410}, {"DC31": 25, "DC32": 30, "DC33": 5}, "PL10",
                 [("RM-PIGMENT-RED", 0.0004, 3), ("RM-WAX-CANDELILLA", 0.0015, 2), ("PK-LIP-CASE", 1, 1)]),
                ("FG-MASCARA-VOL", "Volume Mascara", "EA", 2.2, 1200, {"DC31": 280, "DC32": 240, "DC33": 190}, {"DC31": 12, "DC32": 9, "DC33": 35}, "PL10",
                 [("RM-PIGMENT-BLACK", 0.0006, 3), ("RM-WAX-CANDELILLA", 0.002, 2), ("PK-MASCARA-TUBE", 1, 1.5)])],
        "components": [("RM-SURFACTANT", "Mild surfactant blend", "RPM", "KG", 2.4, 2000), ("RM-KERATIN", "Hydrolysed keratin", "RPM", "KG", 62.0, 60),
                       ("PK-HDPE-400", "400 ml HDPE bottle", "PACK", "EA", 0.21, 20000), ("PK-CAP-FLIP", "Flip-top cap", "PACK", "EA", 0.06, 20000),
                       ("RM-PIGMENT-RED", "Red pigment dispersion", "RPM", "KG", 140.0, 15), ("RM-PIGMENT-BLACK", "Black iron oxide", "RPM", "KG", 38.0, 20),
                       ("RM-WAX-CANDELILLA", "Candelilla wax", "RPM", "KG", 21.0, 120), ("PK-LIP-CASE", "Metal lipstick case", "PACK", "EA", 0.42, 8000),
                       ("PK-MASCARA-TUBE", "Mascara tube + brush", "PACK", "EA", 0.35, 8000)],
        "suppliers": [("Loire Tensioactifs", "FR", "Tours", 47.39, 0.69, "Surfactant sulfonation plant", ["RM-SURFACTANT"], 10, 97, "Rhein Surfactants", 2.4, 260, 8000, "good"),
                      ("Andes Protein Labs", "CL", "Santiago", -33.45, -70.66, "Keratin hydrolysis plant", ["RM-KERATIN"], 38, 92, None, 62.0, 900, 200, "poor"),
                      ("BlowMould Polska", "PL", "Łódź", 51.76, 19.46, "Extrusion blow-moulding", ["PK-HDPE-400", "PK-CAP-FLIP"], 14, 95, "Normandie Packaging", 0.21, 600, 60000, "avg"),
                      ("Colorantes del Norte", "MX", "Monterrey", 25.68, -100.31, "Pigment dispersion plant", ["RM-PIGMENT-RED", "RM-PIGMENT-BLACK"], 30, 93, None, 140.0, 700, 120, "avg"),
                      ("Coahuila Wax Co.", "MX", "Saltillo", 25.42, -101.00, "Candelilla wax refinery", ["RM-WAX-CANDELILLA"], 35, 90, None, 21.0, 650, 1500, "poor"),
                      ("Ningbo Metal Pack", "CN", "Ningbo", 29.87, 121.55, "Aluminium anodising & assembly", ["PK-LIP-CASE", "PK-MASCARA-TUBE"], 45, 90, "Kraków Pack Systems", 0.42, 2600, 50000, "avg")],
        "quotes": [("Rhein Surfactants", "RM-SURFACTANT", 2.6, 300, 8000, 8, True, "DE", "Ludwigshafen", 49.48, 8.44),
                   ("Normandie Packaging", "PK-HDPE-400", 0.24, 500, 60000, 9, True, "FR", "Rouen", 49.44, 1.10),
                   ("Kraków Pack Systems", "PK-LIP-CASE", 0.49, 300, 50000, 12, True, "PL", "Kraków", 50.03, 19.90)],
        "origins": [("Candelilla shrub wax", "Chihuahuan Desert, Mexico", "MX", 27.0, -102.4, "Coahuila Wax Co.", "RM-WAX-CANDELILLA", 100, 10, 6, "high", "wild-harvested; permit-limited volumes"),
                    ("Wool keratin", "Patagonia", "CL", -45.0, -71.0, "Andes Protein Labs", "RM-KERATIN", 70, 12, 5, "medium", "by-product of wool processing")],
        "customers": ["Douglas DE", "Ulta US", "Tmall Global", "Boots UK", "Sephora US", "JD Beauty"],
    },
    ("ecommerce", "shopnova"): {
        "company": "ShopNova Online", "domain": "shopnova-demo.example", "prefix": "SN",
        "plants": [("KT10", "Venlo Kitting Centre", "factory", "NL", "Venlo", 51.37, 6.17), ("KT20", "Poznań Returns & Rework", "contract_manufacturer", "PL", "Poznań", 52.41, 16.93),
                   ("FC01", "Venlo Fulfilment Centre", "warehouse", "NL", "Venlo", 51.39, 6.15), ("FC02", "Dublin Fulfilment Centre", "warehouse", "IE", "Dublin", 53.42, -6.27),
                   ("FC03", "Prague Fulfilment Centre", "warehouse", "CZ", "Prague", 50.10, 14.27)],
        "fgs": [("FG-EARBUDS-KIT", "Wireless earbuds gift kit", "EA", 21.0, 900, {"FC01": 420, "FC02": 180, "FC03": 210}, {"FC01": 9, "FC02": 3, "FC03": 16}, "KT10",
                 [("CM-EARBUDS", 1, 0.5), ("CM-USB-C-CABLE", 1, 0.5), ("PK-GIFT-BOX", 1, 1)]),
                ("FG-PHONE-CASE-15", "Phone case 15 Pro (3-pack)", "EA", 4.1, 1500, {"FC01": 640, "FC02": 300, "FC03": 380}, {"FC01": 14, "FC02": 20, "FC03": 4}, "KT10",
                 [("CM-CASE-TPU", 3, 1), ("PK-POLYBAG", 1, 2)]),
                ("FG-SMART-PLUG-2", "Smart plug twin pack", "EA", 9.8, 700, {"FC01": 250, "FC02": 120, "FC03": 160}, {"FC01": 26, "FC02": 7, "FC03": 11}, "KT20",
                 [("CM-SMART-PLUG", 2, 0.5), ("PK-GIFT-BOX", 1, 1)])],
        "components": [("CM-EARBUDS", "Earbuds pair (bulk)", "PACK", "EA", 14.5, 3000), ("CM-USB-C-CABLE", "USB-C cable 1 m", "PACK", "EA", 0.9, 5000),
                       ("PK-GIFT-BOX", "Printed gift box", "PACK", "EA", 0.45, 8000), ("CM-CASE-TPU", "TPU phone case", "PACK", "EA", 0.8, 15000),
                       ("PK-POLYBAG", "Recycled polybag", "PACK", "EA", 0.03, 30000), ("CM-SMART-PLUG", "Smart plug (bulk)", "PACK", "EA", 3.6, 4000)],
        "suppliers": [("Pearl River Audio", "CN", "Shenzhen", 22.54, 114.06, "Audio OEM factory", ["CM-EARBUDS"], 42, 92, "Hanoi Sound Works", 14.5, 3800, 10000, "poor"),
                      ("Dongguan Cable Co.", "CN", "Dongguan", 23.02, 113.75, "Cable extrusion", ["CM-USB-C-CABLE"], 38, 94, None, 0.9, 1800, 40000, "avg"),
                      ("Eindhoven Print & Pack", "NL", "Eindhoven", 51.44, 5.48, "Litho print & carton", ["PK-GIFT-BOX"], 7, 98, "Wrocław Box", 0.45, 250, 20000, "good"),
                      ("Ho Chi Minh Cases", "VN", "Ho Chi Minh City", 10.82, 106.63, "Injection moulding", ["CM-CASE-TPU"], 40, 90, None, 0.8, 2600, 60000, "avg"),
                      ("GreenFilm Benelux", "BE", "Antwerp", 51.22, 4.40, "Film extrusion", ["PK-POLYBAG"], 5, 98, None, 0.03, 120, 100000, "good"),
                      ("Ningbo SmartHome", "CN", "Ningbo", 29.87, 121.55, "IoT assembly line", ["CM-SMART-PLUG"], 45, 90, None, 3.6, 3000, 15000, "avg")],
        "quotes": [("Hanoi Sound Works", "CM-EARBUDS", 15.4, 3500, 10000, 36, True, "VN", "Hanoi", 21.03, 105.85),
                   ("Wrocław Box", "PK-GIFT-BOX", 0.47, 280, 20000, 6, True, "PL", "Wrocław", 51.11, 17.03)],
        "origins": [("Lithium-ion micro cells", "Guangdong, China", "CN", 23.1, 113.3, "Pearl River Audio", "CM-EARBUDS", 25, 3, 1, "high", "allocation risk in peak season (Q4)")],
        "customers": ["Marketplace orders NL", "Marketplace orders IE", "Marketplace orders CZ", "B2B reseller DE", "Black Friday pre-orders", "Corporate gifting"],
    },
    ("ecommerce", "parcelia"): {
        "company": "Parcelia Marketplace", "domain": "parcelia-demo.example", "prefix": "PM",
        "plants": [("KT40", "Lille Kitting Centre", "factory", "FR", "Lille", 50.63, 3.06), ("FC41", "Lille Fulfilment Centre", "warehouse", "FR", "Lille", 50.60, 3.10),
                   ("FC42", "Madrid Fulfilment Centre", "warehouse", "ES", "Madrid", 40.42, -3.70), ("FC43", "Milan Fulfilment Centre", "warehouse", "IT", "Milan", 45.46, 9.19)],
        "fgs": [("FG-COFFEE-BUNDLE", "Specialty coffee starter bundle", "EA", 11.5, 600, {"FC41": 220, "FC42": 160, "FC43": 190}, {"FC41": 15, "FC42": 5, "FC43": 3}, "KT40",
                 [("CM-COFFEE-BEANS", 1, 0.5), ("CM-MILK-FROTHER", 1, 0.5), ("PK-MAILER-BOX", 1, 1)]),
                ("FG-YOGA-SET", "Yoga starter set", "EA", 8.2, 500, {"FC41": 140, "FC42": 170, "FC43": 120}, {"FC41": 22, "FC42": 8, "FC43": 18}, "KT40",
                 [("CM-YOGA-MAT", 1, 0.5), ("CM-YOGA-BLOCK", 2, 0.5), ("PK-MAILER-BOX", 1, 1)]),
                ("FG-LED-DESK", "LED desk lamp", "EA", 13.0, 400, {"FC41": 95, "FC42": 80, "FC43": 110}, {"FC41": 9, "FC42": 30, "FC43": 6}, "KT40",
                 [("CM-LED-LAMP", 1, 0.5), ("PK-MAILER-BOX", 1, 1)])],
        "components": [("CM-COFFEE-BEANS", "Roasted beans 500 g", "PACK", "EA", 5.2, 3000), ("CM-MILK-FROTHER", "Handheld frother", "PACK", "EA", 2.9, 2000),
                       ("PK-MAILER-BOX", "Corrugated mailer box", "PACK", "EA", 0.38, 15000), ("CM-YOGA-MAT", "TPE yoga mat", "PACK", "EA", 4.1, 2000),
                       ("CM-YOGA-BLOCK", "Cork yoga block", "PACK", "EA", 1.2, 4000), ("CM-LED-LAMP", "LED lamp (bulk)", "PACK", "EA", 8.7, 1500)],
        "suppliers": [("Torrefazione Lombarda", "IT", "Bergamo", 45.70, 9.67, "Roastery", ["CM-COFFEE-BEANS"], 6, 97, None, 5.2, 300, 3000, "good"),
                      ("Zhejiang Kitchenware", "CN", "Yiwu", 29.31, 120.08, "Small appliance assembly", ["CM-MILK-FROTHER"], 44, 90, None, 2.9, 2200, 20000, "poor"),
                      ("Cartonajes del Sur", "ES", "Sevilla", 37.39, -5.98, "Corrugator", ["PK-MAILER-BOX"], 8, 96, "Smurfit Nord", 0.38, 260, 30000, "good"),
                      ("Penang Fitness Goods", "MY", "Penang", 5.41, 100.33, "TPE moulding", ["CM-YOGA-MAT"], 40, 92, None, 4.1, 2400, 8000, "avg"),
                      ("Corticeira do Douro", "PT", "Porto", 41.15, -8.61, "Cork processing", ["CM-YOGA-BLOCK"], 9, 96, None, 1.2, 220, 10000, "good"),
                      ("Foshan Lighting", "CN", "Foshan", 23.02, 113.12, "LED luminaire factory", ["CM-LED-LAMP"], 42, 91, None, 8.7, 2600, 6000, "avg")],
        "quotes": [("Smurfit Nord", "PK-MAILER-BOX", 0.40, 240, 30000, 5, True, "FR", "Arras", 50.29, 2.78)],
        "origins": [("Arabica green coffee", "Minas Gerais, Brazil", "BR", -19.9, -43.9, "Torrefazione Lombarda", "CM-COFFEE-BEANS", 80, 24, 6, "high", "harvest May–Sep; price volatility")],
        "customers": ["Web orders FR", "Web orders ES", "Web orders IT", "Corporate wellness", "Marketplace partners", "Flash sale"],
    },
    ("pharmaceutical", "medivia"): {
        "company": "Medivia Pharma", "domain": "medivia-demo.example", "prefix": "MV",
        "plants": [("PH10", "Cork Oral Solids Plant", "factory", "IE", "Cork", 51.90, -8.47), ("PH20", "Basel Sterile Fill Plant", "factory", "CH", "Basel", 47.56, 7.59),
                   ("DP01", "Rotterdam Pharma DC (GDP)", "warehouse", "NL", "Rotterdam", 51.92, 4.48), ("DP02", "Memphis US DC (GDP)", "warehouse", "US", "Memphis", 35.15, -90.05),
                   ("DP03", "Singapore APAC DC (GDP)", "warehouse", "SG", "Singapore", 1.35, 103.82)],
        "fgs": [("FG-AMOX-500", "Amoxicillin 500 mg caps (box 21)", "EA", 1.9, 6000, {"DP01": 1400, "DP02": 900, "DP03": 600}, {"DP01": 20, "DP02": 6, "DP03": 25}, "PH10",
                 [("API-AMOXICILLIN", 0.0105, 1.5), ("EX-GELATIN-CAPS", 21, 1), ("PK-BLISTER-FOIL", 0.003, 2), ("PK-CARTON-PH", 1, 1)]),
                ("FG-METF-850", "Metformin 850 mg tabs (box 60)", "EA", 1.4, 8000, {"DP01": 1700, "DP02": 2100, "DP03": 900}, {"DP01": 30, "DP02": 18, "DP03": 4}, "PH10",
                 [("API-METFORMIN", 0.051, 1.5), ("PK-BLISTER-FOIL", 0.006, 2), ("PK-CARTON-PH", 1, 1)]),
                ("FG-INSULIN-PEN", "Insulin glargine pen 3 ml (cold chain)", "EA", 7.5, 2500, {"DP01": 420, "DP02": 380, "DP03": 260}, {"DP01": 10, "DP02": 25, "DP03": 7}, "PH20",
                 [("API-INSULIN", 0.0000108, 2), ("PK-PEN-INJECTOR", 1, 1), ("PK-CARTON-PH", 1, 1)])],
        "components": [("API-AMOXICILLIN", "Amoxicillin trihydrate API", "RPM", "KG", 48.0, 300), ("API-METFORMIN", "Metformin HCl API", "RPM", "KG", 9.5, 1200),
                       ("EX-GELATIN-CAPS", "Hard gelatin capsules", "PACK", "EA", 0.004, 600000), ("PK-BLISTER-FOIL", "Alu blister foil", "PACK", "KG", 14.0, 150),
                       ("PK-CARTON-PH", "Pharma folding carton", "PACK", "EA", 0.07, 40000), ("API-INSULIN", "Insulin glargine API", "RPM", "KG", 98000.0, 0.02),
                       ("PK-PEN-INJECTOR", "Pen injector device", "PACK", "EA", 1.8, 15000)],
        "suppliers": [("Hyderabad Fine Chem", "IN", "Hyderabad", 17.39, 78.49, "API synthesis (GMP)", ["API-AMOXICILLIN"], 60, 92, "Shijiazhuang API Works", 48.0, 2200, 2000, "poor"),
                      ("Gujarat API Ltd", "IN", "Vadodara", 22.31, 73.18, "API synthesis (GMP)", ["API-METFORMIN"], 55, 93, None, 9.5, 2000, 8000, "avg"),
                      ("Capsulas Ibéricas", "ES", "Barcelona", 41.39, 2.17, "Capsule moulding", ["EX-GELATIN-CAPS"], 14, 97, None, 0.004, 400, 2000000, "good"),
                      ("Alufoil Westfalen", "DE", "Bielefeld", 52.02, 8.53, "Foil lamination", ["PK-BLISTER-FOIL"], 18, 96, "Amcor Benelux", 14.0, 350, 1500, "good"),
                      ("Dublin Pharma Print", "IE", "Dublin", 53.35, -6.26, "GMP carton printing", ["PK-CARTON-PH"], 7, 98, None, 0.07, 200, 100000, "good"),
                      ("Copenhagen BioAPI", "DK", "Kalundborg", 55.68, 11.09, "Recombinant API (cold chain)", ["API-INSULIN"], 70, 95, None, 98000.0, 5000, 0.2, "avg"),
                      ("Ostrava Devices", "CZ", "Ostrava", 49.82, 18.26, "Injector assembly (ISO 13485)", ["PK-PEN-INJECTOR"], 28, 95, None, 1.8, 900, 40000, "avg")],
        "quotes": [("Shijiazhuang API Works", "API-AMOXICILLIN", 41.0, 3500, 2000, 70, False, "CN", "Shijiazhuang", 38.04, 114.51),
                   ("Amcor Benelux", "PK-BLISTER-FOIL", 14.9, 320, 1500, 12, True, "BE", "Ghent", 51.05, 3.72)],
        "origins": [("Penicillin intermediate 6-APA", "Hebei, China", "CN", 38.0, 114.5, "Hyderabad Fine Chem", "API-AMOXICILLIN", 60, 30, 10, "high", "concentrated global supply; export controls risk")],
        "customers": ["NHS Supply Chain", "McKesson US", "Zuellig Pharma", "Phoenix Group", "Cardinal Health", "Alliance Healthcare"],
        "expiry_days": (300, 900),
    },
    ("pharmaceutical", "bionord"): {
        "company": "BioNord Labs", "domain": "bionord-demo.example", "prefix": "BN",
        "plants": [("BN10", "Uppsala Biologics Plant", "factory", "SE", "Uppsala", 59.86, 17.64), ("BN21", "Stockholm Nordic DC", "warehouse", "SE", "Stockholm", 59.33, 18.07),
                   ("BN22", "Hamburg EU DC", "warehouse", "DE", "Hamburg", 53.55, 9.99), ("BN23", "Boston US DC", "warehouse", "US", "Boston", 42.36, -71.06)],
        "fgs": [("FG-VACC-FLU", "Influenza vaccine prefilled syringe", "EA", 4.2, 10000, {"BN21": 900, "BN22": 2400, "BN23": 1800}, {"BN21": 30, "BN22": 5, "BN23": 12}, "BN10",
                 [("API-ANTIGEN-FLU", 0.0000005, 3), ("PK-SYRINGE-PF", 1, 1.5), ("PK-CARTON-PH", 1, 1)]),
                ("FG-MAB-200", "Monoclonal antibody 200 mg vial", "EA", 310.0, 300, {"BN21": 20, "BN22": 45, "BN23": 60}, {"BN21": 40, "BN22": 14, "BN23": 4}, "BN10",
                 [("API-MAB", 0.0002, 2), ("PK-VIAL-10ML", 1, 1), ("PK-CARTON-PH", 1, 1)]),
                ("FG-SALINE-FLUSH", "Saline flush syringe 10 ml", "EA", 0.35, 20000, {"BN21": 3000, "BN22": 5200, "BN23": 4100}, {"BN21": 18, "BN22": 25, "BN23": 9}, "BN10",
                 [("RM-SALINE-WFI", 0.0105, 1), ("PK-SYRINGE-PF", 1, 1.5)])],
        "components": [("API-ANTIGEN-FLU", "Flu antigen bulk", "RPM", "KG", 2400000.0, 0.002), ("PK-SYRINGE-PF", "Prefilled syringe barrel", "PACK", "EA", 0.18, 150000),
                       ("PK-CARTON-PH", "Pharma folding carton", "PACK", "EA", 0.07, 50000), ("API-MAB", "Antibody drug substance", "RPM", "KG", 900000.0, 0.02),
                       ("PK-VIAL-10ML", "Type I glass vial 10 ml", "PACK", "EA", 0.22, 30000), ("RM-SALINE-WFI", "Saline WFI bulk", "RPM", "KG", 0.6, 4000)],
        "suppliers": [("Leiden Antigen BV", "NL", "Leiden", 52.16, 4.49, "Egg-free antigen production", ["API-ANTIGEN-FLU"], 45, 95, None, 2400000.0, 3000, 0.01, "avg"),
                      ("Schott-type Glass Mainz", "DE", "Mainz", 49.99, 8.25, "Tubular glass converting", ["PK-SYRINGE-PF", "PK-VIAL-10ML"], 21, 94, "Gerresheimer-type Pilsen", 0.18, 900, 200000, "poor"),
                      ("Göteborg Pharma Print", "SE", "Gothenburg", 57.71, 11.97, "GMP carton printing", ["PK-CARTON-PH"], 6, 98, None, 0.07, 200, 100000, "good"),
                      ("Cambridge MAb CDMO", "GB", "Cambridge", 52.20, 0.12, "Biologics CDMO", ["API-MAB"], 90, 92, None, 900000.0, 8000, 0.1, "avg"),
                      ("Aarhus Fluids", "DK", "Aarhus", 56.16, 10.20, "WFI production", ["RM-SALINE-WFI"], 5, 98, None, 0.6, 150, 20000, "good")],
        "quotes": [("Gerresheimer-type Pilsen", "PK-SYRINGE-PF", 0.20, 700, 200000, 18, True, "CZ", "Plzeň", 49.74, 13.38)],
        "origins": [("Borosilicate glass tubing", "Bavaria, Germany", "DE", 49.0, 12.1, "Schott-type Glass Mainz", "PK-SYRINGE-PF", 100, 3, 1, "high", "industry-wide tubing capacity constraint")],
        "customers": ["Swedish Region Stockholm", "Bundeswehr Sanitätsdienst", "US CDC programme", "Apoteket", "Hospital group DE", "IDN Boston"],
        "expiry_days": (200, 700),
    },
    ("automotive", "voltara"): {
        "company": "Voltara Motors", "domain": "voltara-demo.example", "prefix": "VM",
        "plants": [("AU10", "Zwickau EV Battery Plant", "factory", "DE", "Zwickau", 50.72, 12.50), ("AU20", "Puebla Drive-unit Plant", "factory", "MX", "Puebla", 19.04, -98.21),
                   ("AD01", "Leipzig Parts DC", "warehouse", "DE", "Leipzig", 51.34, 12.37), ("AD02", "Laredo US Parts DC", "warehouse", "US", "Laredo", 27.53, -99.48),
                   ("AD03", "Tianjin Parts DC", "warehouse", "CN", "Tianjin", 39.08, 117.20)],
        "fgs": [("FG-BATT-MOD-48", "48 V battery module", "EA", 410.0, 150, {"AD01": 120, "AD02": 60, "AD03": 45}, {"AD01": 6, "AD02": 14, "AD03": 3}, "AU10",
                 [("CM-CELL-NMC", 96, 0.5), ("CM-BMS-PCB", 1, 1), ("CM-HOUSING-AL", 1, 1)]),
                ("FG-INVERTER-SIC", "SiC traction inverter", "EA", 520.0, 80, {"AD01": 40, "AD02": 55, "AD03": 25}, {"AD01": 20, "AD02": 5, "AD03": 30}, "AU20",
                 [("CM-SIC-MOSFET", 24, 1), ("CM-BMS-PCB", 1, 1), ("CM-HOUSING-AL", 1, 1)]),
                ("FG-CHARGER-11KW", "11 kW onboard charger", "EA", 180.0, 120, {"AD01": 70, "AD02": 45, "AD03": 50}, {"AD01": 11, "AD02": 9, "AD03": 4}, "AU20",
                 [("CM-SIC-MOSFET", 8, 1), ("CM-CHARGER-PCB", 1, 1), ("CM-HOUSING-AL", 1, 1)])],
        "components": [("CM-CELL-NMC", "NMC pouch cell 60 Ah", "PACK", "EA", 3.4, 20000), ("CM-BMS-PCB", "BMS control PCB", "PACK", "EA", 38.0, 800),
                       ("CM-HOUSING-AL", "Die-cast aluminium housing", "PACK", "EA", 46.0, 600), ("CM-SIC-MOSFET", "SiC power MOSFET", "PACK", "EA", 9.5, 4000),
                       ("CM-CHARGER-PCB", "Charger power board", "PACK", "EA", 52.0, 500)],
        "suppliers": [("Gyeonggi Cell Energy", "KR", "Cheongju", 36.64, 127.49, "Cell gigafactory", ["CM-CELL-NMC"], 56, 95, "Silesia Cell Plant", 3.4, 6000, 100000, "avg"),
                      ("Brno Electronics", "CZ", "Brno", 49.20, 16.61, "PCBA SMT lines", ["CM-BMS-PCB", "CM-CHARGER-PCB"], 12, 96, None, 38.0, 400, 3000, "good"),
                      ("Saxony Castings", "DE", "Chemnitz", 50.83, 12.92, "High-pressure die casting", ["CM-HOUSING-AL"], 9, 97, "Querétaro Castings", 46.0, 300, 2000, "good"),
                      ("Kyushu Power Semi", "JP", "Kumamoto", 32.80, 130.74, "SiC wafer fab + backend", ["CM-SIC-MOSFET"], 84, 90, None, 9.5, 2500, 40000, "poor")],
        "quotes": [("Silesia Cell Plant", "CM-CELL-NMC", 3.7, 1500, 100000, 21, True, "PL", "Wrocław", 51.11, 17.03),
                   ("Querétaro Castings", "CM-HOUSING-AL", 43.0, 500, 2000, 10, True, "MX", "Querétaro", 20.59, -100.39)],
        "origins": [("Lithium hydroxide", "Western Australia", "AU", -32.0, 116.0, "Gyeonggi Cell Energy", "CM-CELL-NMC", 30, 35, 8, "high", "price & offtake volatility"),
                    ("Nickel sulphate", "Sulawesi, Indonesia", "ID", -2.0, 121.0, "Gyeonggi Cell Energy", "CM-CELL-NMC", 25, 20, 6, "high", "ESG scrutiny"),
                    ("SiC substrate wafers", "North Carolina, USA", "US", 35.9, -78.9, "Kyushu Power Semi", "CM-SIC-MOSFET", 60, 18, 5, "high", "single-region substrate supply")],
        "customers": ["Line feed Zwickau assembly", "OEM customer Stuttgart", "Fleet retrofit US", "OEM customer Shanghai", "Service parts EU", "OEM customer Detroit"],
    },
    ("automotive", "kestrel"): {
        "company": "Kestrel Automotive", "domain": "kestrel-demo.example", "prefix": "KA",
        "plants": [("KA10", "Győr Brake Systems Plant", "factory", "HU", "Győr", 47.69, 17.63), ("KA21", "Bratislava Parts DC", "warehouse", "SK", "Bratislava", 48.15, 17.11),
                   ("KA22", "Valencia Parts DC", "warehouse", "ES", "Valencia", 39.47, -0.38), ("KA23", "Bursa Parts DC", "warehouse", "TR", "Bursa", 40.19, 29.06)],
        "fgs": [("FG-BRAKE-CAL", "Brake caliper assembly", "EA", 64.0, 600, {"KA21": 380, "KA22": 260, "KA23": 210}, {"KA21": 4, "KA22": 16, "KA23": 9}, "KA10",
                 [("CM-CAL-CASTING", 1, 1.5), ("CM-PISTON", 2, 0.5), ("CM-SEAL-KIT", 1, 1)]),
                ("FG-BRAKE-DISC", "Ventilated brake disc 340 mm", "EA", 28.0, 900, {"KA21": 520, "KA22": 410, "KA23": 300}, {"KA21": 12, "KA22": 3, "KA23": 20}, "KA10",
                 [("CM-DISC-BLANK", 1, 2)]),
                ("FG-ABS-SENSOR", "ABS wheel-speed sensor", "EA", 11.0, 1500, {"KA21": 900, "KA22": 640, "KA23": 520}, {"KA21": 18, "KA22": 22, "KA23": 5}, "KA10",
                 [("CM-HALL-IC", 1, 1), ("CM-SENSOR-HOUSING", 1, 1)])],
        "components": [("CM-CAL-CASTING", "Caliper iron casting", "PACK", "EA", 18.0, 3000), ("CM-PISTON", "Phenolic piston", "PACK", "EA", 2.1, 8000),
                       ("CM-SEAL-KIT", "Seal & boot kit", "PACK", "EA", 1.4, 6000), ("CM-DISC-BLANK", "Grey-iron disc blank", "PACK", "EA", 11.0, 4000),
                       ("CM-HALL-IC", "Hall-effect IC", "PACK", "EA", 0.9, 20000), ("CM-SENSOR-HOUSING", "Over-moulded sensor housing", "PACK", "EA", 1.7, 8000)],
        "suppliers": [("Ostrava Foundry", "CZ", "Ostrava", 49.82, 18.26, "Ductile iron foundry", ["CM-CAL-CASTING", "CM-DISC-BLANK"], 14, 95, "Bursa Döküm", 18.0, 600, 4000, "avg"),
                      ("Stuttgart Polymer Tech", "DE", "Stuttgart", 48.78, 9.18, "Phenolic moulding", ["CM-PISTON"], 10, 97, None, 2.1, 250, 20000, "good"),
                      ("Turin Sealing", "IT", "Turin", 45.07, 7.69, "Elastomer moulding", ["CM-SEAL-KIT"], 12, 96, None, 1.4, 260, 15000, "good"),
                      ("Penang Semiconductor", "MY", "Penang", 5.41, 100.33, "Sensor IC backend", ["CM-HALL-IC"], 70, 90, None, 0.9, 1800, 100000, "poor"),
                      ("Brno Plastics", "CZ", "Brno", 49.20, 16.61, "Insert moulding", ["CM-SENSOR-HOUSING"], 8, 97, None, 1.7, 220, 20000, "good")],
        "quotes": [("Bursa Döküm", "CM-DISC-BLANK", 9.9, 900, 4000, 16, True, "TR", "Bursa", 40.18, 29.07)],
        "origins": [("Pig iron & scrap steel", "Silesia, Poland", "PL", 50.3, 19.0, "Ostrava Foundry", "CM-CAL-CASTING", 90, 2, 1, "medium", "energy-price exposure")],
        "customers": ["OEM line feed Bratislava", "Aftermarket ES", "OEM line feed Bursa", "Aftermarket TR", "OEM customer Valencia", "Fleet service EU"],
    },
    ("food", "verdant"): {
        "company": "Verdant Foods", "domain": "verdant-demo.example", "prefix": "VF",
        "plants": [("VF10", "Bremen Chocolate Plant", "factory", "DE", "Bremen", 53.08, 8.80), ("VF21", "Duisburg Ambient DC", "warehouse", "DE", "Duisburg", 51.43, 6.76),
                   ("VF22", "Lyon Ambient DC", "warehouse", "FR", "Lyon", 45.76, 4.84), ("VF23", "Felixstowe UK DC", "warehouse", "GB", "Felixstowe", 51.96, 1.35)],
        "fgs": [("FG-DARK-70", "Dark chocolate 70% 100 g", "EA", 0.85, 20000, {"VF21": 6200, "VF22": 4100, "VF23": 3900}, {"VF21": 9, "VF22": 21, "VF23": 4}, "VF10",
                 [("RM-COCOA-MASS", 0.07, 1), ("RM-SUGAR", 0.03, 1), ("PK-FLOWWRAP", 0.0012, 3)]),
                ("FG-HAZEL-SPREAD", "Hazelnut spread 400 g", "EA", 1.6, 9000, {"VF21": 2400, "VF22": 2900, "VF23": 1500}, {"VF21": 14, "VF22": 5, "VF23": 18}, "VF10",
                 [("RM-HAZELNUT", 0.13, 1), ("RM-SUGAR", 0.2, 1), ("RM-COCOA-MASS", 0.03, 1), ("PK-GLASS-JAR", 1, 1.5)]),
                ("FG-PROTEIN-BAR", "Protein bar 45 g", "EA", 0.55, 15000, {"VF21": 3800, "VF22": 2200, "VF23": 2600}, {"VF21": 25, "VF22": 11, "VF23": 7}, "VF10",
                 [("RM-WHEY", 0.015, 1), ("RM-COCOA-MASS", 0.006, 1), ("PK-FLOWWRAP", 0.0006, 3)])],
        "components": [("RM-COCOA-MASS", "Cocoa mass", "RPM", "KG", 7.8, 20000), ("RM-SUGAR", "Beet sugar", "RPM", "KG", 0.75, 60000),
                       ("PK-FLOWWRAP", "Flow-wrap film", "PACK", "KG", 4.2, 4000), ("RM-HAZELNUT", "Roasted hazelnut paste", "RPM", "KG", 9.4, 15000),
                       ("PK-GLASS-JAR", "400 g glass jar + lid", "PACK", "EA", 0.19, 60000), ("RM-WHEY", "Whey protein isolate", "RPM", "KG", 11.5, 5000)],
        "suppliers": [("Amsterdam Cocoa Processing", "NL", "Amsterdam", 52.39, 4.83, "Cocoa grinding", ["RM-COCOA-MASS"], 12, 96, "Hamburg Cocoa", 7.8, 600, 20000, "avg"),
                      ("Niedersachsen Sugar", "DE", "Uelzen", 52.97, 10.56, "Beet sugar factory", ["RM-SUGAR"], 5, 98, None, 0.75, 400, 60000, "good"),
                      ("Flexpack Rhein", "DE", "Cologne", 50.94, 6.96, "Film printing & lamination", ["PK-FLOWWRAP"], 10, 97, None, 4.2, 300, 5000, "good"),
                      ("Black Sea Hazelnut", "TR", "Ordu", 40.98, 37.88, "Hazelnut roasting", ["RM-HAZELNUT"], 28, 91, "Piemonte Nocciole", 9.4, 2400, 20000, "poor"),
                      ("Vidrios del Ebro", "ES", "Zaragoza", 41.65, -0.89, "Glass container furnace", ["PK-GLASS-JAR"], 14, 95, None, 0.19, 900, 120000, "avg"),
                      ("Irish Dairy Proteins", "IE", "Kilkenny", 52.65, -7.25, "Membrane filtration", ["RM-WHEY"], 18, 95, None, 11.5, 700, 8000, "avg")],
        "quotes": [("Hamburg Cocoa", "RM-COCOA-MASS", 8.1, 400, 20000, 7, True, "DE", "Hamburg", 53.55, 9.99),
                   ("Piemonte Nocciole", "RM-HAZELNUT", 11.2, 600, 20000, 9, True, "IT", "Alba", 44.70, 8.03)],
        "origins": [("Cocoa beans", "Côte d'Ivoire", "CI", 6.8, -5.3, "Amsterdam Cocoa Processing", "RM-COCOA-MASS", 60, 21, 7, "high", "EUDR deforestation compliance; mid-crop variability"),
                    ("Cocoa beans", "Ghana", "GH", 6.7, -1.6, "Amsterdam Cocoa Processing", "RM-COCOA-MASS", 25, 20, 6, "high", "EUDR compliance"),
                    ("Hazelnuts", "Black Sea coast, Türkiye", "TR", 41.0, 38.0, "Black Sea Hazelnut", "RM-HAZELNUT", 100, 3, 2, "high", "frost risk in spring")],
        "customers": ["Rewe Group", "Carrefour France", "Tesco UK", "Edeka", "Intermarché", "Sainsbury's"],
        "expiry_days": (60, 400),
    },
}
INDUSTRIES = {"cosmetics": "Cosmetics & beauty", "ecommerce": "E-commerce & retail", "pharmaceutical": "Pharmaceutical", "automotive": "Automotive", "food": "Food & beverage"}
ZONE.update({"PT": "Europe", "DK": "Europe", "HU": "Europe", "SK": "Europe", "TR": "Europe", "ID": "Asia-Pacific"})


def iso(days: int) -> str:
    return (AS_OF + timedelta(days=days)).isoformat()


def person(rng: random.Random, domain: str, role: str, phone_cc: str, i: int, primary: bool) -> dict:
    first, last = rng.choice(FIRST), rng.choice(LAST)
    email = f"{first}.{last}".lower().replace("é", "e").replace("ó", "o") + f"@{domain}"
    return {"role": role, "name": f"{first} {last}", "email": email, "phone": f"{phone_cc} 555 01{i:02d}", "primary": primary}


def build(industry: str, customer: str, spec: dict) -> dict:
    rng = random.Random(f"{industry}/{customer}")
    prefix = spec["prefix"]
    cc = {"FR": "+33", "DE": "+49", "PL": "+48", "US": "+1", "CN": "+86", "NL": "+31", "IE": "+353", "CZ": "+420", "ES": "+34", "IT": "+39", "CH": "+41",
          "SG": "+65", "SE": "+46", "MX": "+52", "HU": "+36", "SK": "+421", "TR": "+90", "GB": "+44"}
    plants = []
    for code, name, ptype, country, city, lat, lon in spec["plants"]:
        roles = ["Warehouse manager", "Inventory control lead", "Transport coordinator"] if ptype == "warehouse" else ["Plant manager", "Production planning lead", "Quality lead"]
        plants.append({"code": code, "name": name, "type": ptype, "country": country, "lat": lat, "lon": lon, "city": city, "zone": ZONE[country],
                       "address": f"{city}, {country} (demo address)", "timezone": "local", "operating_hours": "Mon–Fri 06:00–22:00" if ptype != "warehouse" else "Mon–Sat 06:00–22:00",
                       "contacts": [person(rng, spec["domain"], r, cc.get(country, "+00"), i, i == 0) for i, r in enumerate(roles)],
                       "contacts_note": "Fictional demo contacts (reserved .example domain)."})
    dcs = [p["code"] for p in plants if p["type"] == "warehouse"]
    materials = [{"code": c, "description": d, "type": "FG", "uom": u, "unit_cost": cost, "safety_stock": safety} for c, d, u, cost, safety, *_ in spec["fgs"]]
    materials += [{"code": c, "description": d, "type": t, "uom": u, "unit_cost": cost, "safety_stock": safety} for c, d, t, u, cost, safety in spec["components"]]
    comp = {m["code"]: m for m in materials}
    bom, demand, stock, production, sales, shipments = [], {}, [], [], [], []
    expiry_range = spec.get("expiry_days")
    exp = (lambda: iso(rng.randint(*expiry_range))) if expiry_range else (lambda: None)
    for n, (fg, _desc, _uom, _cost, _safety, dem, cover, plant, lines) in enumerate(spec["fgs"]):
        demand[fg] = dem
        for component, qty, scrap in lines:
            bom.append({"plant": plant, "parent": fg, "component": component, "quantity": qty, "scrap_pct": scrap})
        for dc in dcs:
            # Keep the demo readable: only the first product carries the low-cover hotspots from the spec.
            days = cover[dc] if n == 0 else max(cover[dc], 24)
            stock.append({"plant": dc, "material": fg, "batch": f"{fg[3:9]}-{dc}", "quantity": round(dem[dc] * days), "status": "unrestricted", "expiry": exp()})
        run = round(sum(dem.values()) * rng.choice([10, 12, 14, 18]), -1)
        production.append({"order": f"1{prefix}{n:02d}01", "plant": plant, "material": fg, "quantity": run, "finish_date": iso(rng.randint(6, 12)), "status": "released"})
        production.append({"order": f"1{prefix}{n:02d}02", "plant": plant, "material": fg, "quantity": round(run * 1.3, -1), "finish_date": iso(rng.randint(15, 24)), "status": "planned"})
    # component stock at the producing plants: some short on purpose
    for line in bom:
        need = sum(o["quantity"] for o in production if o["material"] == line["parent"] and o["status"] == "released") * line["quantity"]
        if any(s["plant"] == line["plant"] and s["material"] == line["component"] for s in stock):
            continue
        factor = rng.choice([0.45, 0.7, 1.1, 1.4, 1.8])
        unit = comp[line["component"]]["uom"]
        qty = round(need * factor) if unit == "EA" else round(need * factor, 3)
        stock.append({"plant": line["plant"], "material": line["component"], "batch": f"{line['component'][3:9]}-A", "quantity": qty, "status": "unrestricted", "expiry": exp()})
    # suppliers, POs, receipt history
    suppliers, pos, history, lots = [], [], [], []
    profile_delay = {"good": [0, 0, 1], "avg": [0, 3, 6], "poor": [5, 11, 16]}
    for i, (name, country, city, lat, lon, site, mats, lead, otif, secondary, price, freight, oq, profile) in enumerate(spec["suppliers"]):
        code = f"V-{prefix}{i + 1:03d}"
        suppliers.append({"code": code, "name": name, "country": country, "materials": mats, "contract_lead_time_days": lead, "otif_target_pct": otif, "approved": True,
                          "secondary_source": secondary, "unit_price_eur": price, "freight_eur_per_order": freight, "typical_order_qty": oq, "lat": lat, "lon": lon, "city": city,
                          "manufacturing_country": country, "manufacturing_site": site, "zone": ZONE[country]})
        for m in mats:
            plant = next((b["plant"] for b in bom if b["component"] == m), plants[0]["code"])
            need = sum(o["quantity"] for o in production if o["plant"] == plant) * next(b["quantity"] for b in bom if b["component"] == m)
            unit = comp[m]["uom"]
            qty1 = round(need * 0.35) if unit == "EA" else round(need * 0.35, 3)
            pos.append({"po": f"45{prefix}{len(pos) + 1:05d}", "supplier": name, "material": m, "plant": plant, "quantity": qty1, "delivery_date": iso(rng.randint(3, 9)), "status": "confirmed"})
            pos.append({"po": f"45{prefix}{len(pos) + 1:05d}", "supplier": name, "material": m, "plant": plant, "quantity": qty1, "delivery_date": iso(rng.randint(16, 30)),
                        "status": "confirmed" if rng.random() > 0.25 else "unconfirmed"})
            for k, delay in enumerate(profile_delay[profile]):
                ordered = qty1 or 1
                rejected = round(ordered * (0.08 if profile == "poor" and k == 1 else 0), 3)
                promised = iso(-150 + 50 * k)
                history.append({"po": f"44{prefix}{len(history) + 1:05d}", "supplier": name, "material": m, "promised_date": promised,
                                "received_date": (date.fromisoformat(promised) + timedelta(days=delay)).isoformat(), "quantity_ordered": ordered,
                                "quantity_received": ordered, "quality_rejected": rejected})
        if profile == "poor":
            m = mats[0]
            plant = next((b["plant"] for b in bom if b["component"] == m), plants[0]["code"])
            q = round(max(1, next(s["quantity"] for s in stock if s["material"] == m) * 0.3), 3)
            lots.append({"lot": f"QL-{prefix}{len(lots) + 1:04d}", "plant": plant, "material": m, "batch": f"{m[3:9]}-Q", "quantity": q, "supplier": name, "status": "blocked",
                         "usage_decision": "rejected", "expected_release": None, "defect": "Out-of-specification on incoming inspection"})
            stock.append({"plant": plant, "material": m, "batch": f"{m[3:9]}-Q", "quantity": q, "status": "blocked", "expiry": exp()})
    m = spec["components"][0][0]
    plant = next(b["plant"] for b in bom if b["component"] == m)
    q = round(max(1, next(s["quantity"] for s in stock if s["material"] == m) * 0.15), 3)
    lots.append({"lot": f"QL-{prefix}{len(lots) + 1:04d}", "plant": plant, "material": m, "batch": f"{m[3:9]}-QI", "quantity": q, "supplier": spec["suppliers"][0][0],
                 "status": "inspection", "usage_decision": None, "expected_release": iso(3), "defect": None})
    stock.append({"plant": plant, "material": m, "batch": f"{m[3:9]}-QI", "quantity": q, "status": "quality_inspection", "expiry": exp()})
    # sales orders: one per customer, sized against DC stock so a few are at risk
    fgs = [f[0] for f in spec["fgs"]]
    for i, cust in enumerate(spec["customers"]):
        fg, dc = fgs[i % len(fgs)], dcs[i % len(dcs)]
        on_hand = next(s["quantity"] for s in stock if s["plant"] == dc and s["material"] == fg)
        qty = round(on_hand * (1.25 if i == 0 else rng.choice([0.15, 0.25, 0.35])), -1)  # one order deliberately short
        sales.append({"order": f"SO-{prefix}{7700 + i}", "customer": cust, "warehouse": dc, "material": fg, "quantity": qty, "requested_date": iso(rng.randint(5, 14)),
                      "priority": "high" if i % 3 == 0 else "standard"})
    # lanes between every DC pair (cost/lead by zone)
    lanes = []
    zone_of = {p["code"]: p["zone"] for p in plants}
    for a in dcs:
        for b in dcs:
            if a != b:
                same = zone_of[a] == zone_of[b]
                lanes.append({"from": a, "to": b, "lead_days": rng.choice([2, 3]) if same else rng.choice([9, 14, 21]),
                              "cost_per_unit": round((0.4 if same else 1.6) * (1 + rng.random() / 3), 2), "carbon_kg_per_unit": round((0.06 if same else 0.4) * (1 + rng.random() / 3), 3)})
    carriers = ["DHL Freight", "Maersk", "DB Schenker", "Kuehne+Nagel", "DSV Road", "CMA CGM"]
    shipments.append({"shipment": f"SH-{prefix}01", "type": "stock_transfer", "from": dcs[0], "to": dcs[1], "material": fgs[0], "quantity": round(demand[fgs[0]][dcs[1]] * 3, -1),
                      "carrier": carriers[0], "mode": "road", "departed": iso(-3), "eta": iso(1), "status": "in_transit", "delay_days": 2, "delay_reason": "Border congestion"})
    shipments.append({"shipment": f"SH-{prefix}02", "type": "stock_transfer", "from": dcs[0], "to": dcs[-1], "material": fgs[1], "quantity": round(demand[fgs[1]][dcs[-1]] * 4, -1),
                      "carrier": carriers[1], "mode": "sea", "departed": iso(-12), "eta": iso(4), "status": "in_transit", "delay_days": 6, "delay_reason": "Port congestion"})
    first_sup = suppliers[0]
    shipments.append({"shipment": f"SH-{prefix}03", "type": "inbound", "from": first_sup["code"], "to": next(b["plant"] for b in bom if b["component"] in first_sup["materials"]),
                      "material": first_sup["materials"][0], "quantity": pos[0]["quantity"], "carrier": carriers[2], "mode": "road", "departed": iso(-1), "eta": pos[0]["delivery_date"],
                      "status": "in_transit", "delay_days": 0, "delay_reason": None})
    # stocktake counts + goods movements (one explained, one within tolerance, one to investigate, one matched)
    fg_rows = [s for s in stock if s["material"] in fgs and s["plant"] in dcs]
    a, b, c, d = fg_rows[0], fg_rows[1], fg_rows[2], fg_rows[3]
    counts = [
        {"count_id": f"PI-{prefix}-01", "count_date": iso(-1), "plant": a["plant"], "material": a["material"], "batch": a["batch"], "book_quantity": a["quantity"], "counted_quantity": a["quantity"] - 40, "counter": "Night shift"},
        {"count_id": f"PI-{prefix}-02", "count_date": iso(-1), "plant": b["plant"], "material": b["material"], "batch": b["batch"], "book_quantity": b["quantity"], "counted_quantity": b["quantity"] - max(1, round(b["quantity"] * 0.004)), "counter": "Cycle count A"},
        {"count_id": f"PI-{prefix}-03", "count_date": iso(-1), "plant": c["plant"], "material": c["material"], "batch": c["batch"], "book_quantity": c["quantity"], "counted_quantity": round(c["quantity"] * 0.96), "counter": "Cycle count B"},
        {"count_id": f"PI-{prefix}-04", "count_date": iso(-1), "plant": d["plant"], "material": d["material"], "batch": d["batch"], "book_quantity": d["quantity"], "counted_quantity": d["quantity"], "counter": "Cycle count C"},
    ]
    movements = [{"document": f"49{prefix}0001", "type": "goods_issue", "plant": a["plant"], "material": a["material"], "batch": a["batch"], "quantity": -40, "date": iso(-2),
                  "posted": False, "reference": "Samples issued, posting pending"}]
    snapshot = {"id": f"SAP-{prefix}-2026-10-20T040000Z", "source_system": f"S4HANA-{industry.upper()}-DEMO", "extracted_at": "2026-10-20T04:00:00+00:00",
                "as_of_date": AS_OF.isoformat(), "read_only": True, "modules": ["MM", "PP", "QM", "SD", "PUR", "WM", "LE"],
                "industry": industry, "customer": spec["company"], "synthetic": True}
    quotes = [{"supplier": s, "material": m, "unit_price_eur": p, "freight_eur_per_order": f, "typical_order_qty": q, "quoted_lead_time_days": lt, "qualified": ok,
               "country": c2, "city": city, "lat": lat, "lon": lon, "zone": ZONE[c2], "reference": "approved secondary source" if ok else "qualification in progress"}
              for s, m, p, f, q, lt, ok, c2, city, lat, lon in spec["quotes"]]
    origins = [{"ingredient": ing, "origin": o, "country": c2, "lat": lat, "lon": lon, "feeds_supplier": fs, "feeds_material": fm, "share_of_material_pct": sh, "transit_days": t,
                "transit_variability_days": v, "criticality": crit, "alternatives": "see sourcing plan", "note": note}
               for ing, o, c2, lat, lon, fs, fm, sh, t, v, crit, note in spec["origins"]]
    return {"snapshot": snapshot, "plants": plants, "materials": materials, "suppliers": suppliers, "bom": bom, "stock": stock, "purchase_orders": pos,
            "po_history": history, "production_orders": production, "quality_lots": lots, "sales_orders": sales, "shipments": shipments,
            "stocktake_counts": counts, "goods_movements": movements, "warehouse_demand_daily": demand, "lanes": lanes, "supplier_quotes": quotes,
            "ingredient_origins": origins}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"default": "cosmetics/aurelia", "industries": {k: {"label": v, "customers": []} for k, v in INDUSTRIES.items()}}
    index["industries"]["cosmetics"]["customers"].append({"id": "aurelia", "name": "Aurelia Cosmetics", "file": "data/sap_mock.json", "synthetic": True})
    for (industry, customer), spec in SPECS.items():
        data = build(industry, customer, spec)
        file = OUT / f"{industry}__{customer}.json"
        file.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        index["industries"][industry]["customers"].append({"id": customer, "name": spec["company"], "file": f"data/tenants/{file.name}", "synthetic": True})
        print(f"{industry:15} {spec['company']:28} {len(data['materials'])} materials, {len(data['suppliers'])} suppliers, {len(data['plants'])} sites")
    (OUT / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
