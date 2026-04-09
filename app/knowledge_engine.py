"""
SmartFarm AI — Comprehensive Agricultural Knowledge Engine
===========================================================
Maps every PlantVillage class to expert-level agronomic data:
  crop, disease, cause, severity, solution, prevention, irrigation, soil.

NEVER returns "Unknown" — every class has a validated knowledge entry.
"""

# ── Crop → Valid Diseases mapping (two-stage validation) ──────────────────
# Only these disease/crop combinations are valid. If the model predicts a
# disease that doesn't belong to the identified crop, the result is rejected.
CROP_DISEASE_MAP = {
    "Apple": [
        "Apple Scab", "Black Rot", "Cedar Apple Rust", None,  # None = healthy
    ],
    "Blueberry": [None],
    "Cherry": ["Powdery Mildew", None],
    "Corn": [
        "Cercospora Leaf Spot (Gray Leaf Spot)", "Common Rust",
        "Northern Leaf Blight", None,
    ],
    "Grape": [
        "Black Rot", "Esca (Black Measles)",
        "Leaf Blight (Isariopsis Leaf Spot)", None,
    ],
    "Orange": ["Huanglongbing (Citrus Greening)"],
    "Peach": ["Bacterial Spot", None],
    "Pepper": ["Bacterial Spot", None],
    "Potato": ["Early Blight", "Late Blight", None],
    "Raspberry": [None],
    "Soybean": [None],
    "Squash": ["Powdery Mildew"],
    "Strawberry": ["Leaf Scorch", None],
    "Tomato": [
        "Bacterial Spot", "Early Blight", "Late Blight", "Leaf Mold",
        "Septoria Leaf Spot", "Spider Mites (Two-Spotted Spider Mite)",
        "Target Spot", "Yellow Leaf Curl Virus", "Mosaic Virus", None,
    ],
}

# ── Full Knowledge Base — keyed by PlantVillage class name ────────────────
# Every single one of the 39 classes (minus Background) is covered.
KNOWLEDGE_BASE = {
    # ═══════════════════════ APPLE ═══════════════════════════════════════
    "Apple___Apple_scab": {
        "crop": "Apple",
        "disease": "Apple Scab",
        "cause": "Fungal infection (Venturia inaequalis) — spreads through rain splash on fallen infected leaves during cool, wet spring weather",
        "severity": "High",
        "solution": "Apply captan or myclobutanil fungicide at green-tip stage. Remove and destroy fallen leaves. Prune infected branches for airflow.",
        "prevention": "Plant scab-resistant varieties (Liberty, Enterprise). Rake and destroy fallen leaves in autumn. Apply preventive fungicide spray schedule from bud break through petal fall.",
        "organic": "Sulfur-based sprays or neem oil applied every 7-10 days during wet periods. Compost tea foliar spray to boost leaf immunity.",
        "chemical": "Captan 50WP (2g/L) or Myclobutanil 40WP (0.5g/L) every 10-14 days during infection period",
        "dosage": "Captan: 2g per litre, spray every 10 days from bud break to 2 weeks after petal fall",
        "irrigation": "Avoid overhead irrigation. Use drip irrigation to keep foliage dry.",
        "soil_correction": "Maintain soil pH 6.0-7.0. Apply lime if too acidic. Ensure proper drainage.",
    },
    "Apple___Black_rot": {
        "crop": "Apple",
        "disease": "Black Rot",
        "cause": "Fungal infection (Botryosphaeria obtusa) — enters through wounds, cankers, or fire blight damage; favoured by warm, humid conditions",
        "severity": "High",
        "solution": "Prune and destroy all cankers and mummified fruit. Apply thiophanate-methyl or captan fungicide. Remove dead wood each winter.",
        "prevention": "Remove all mummified fruit and dead wood. Practice strict orchard sanitation. Avoid wounding trees during cultivation.",
        "organic": "Copper hydroxide spray at dormant and green-tip stages. Remove all infected tissue promptly.",
        "chemical": "Thiophanate-methyl (Topsin-M) 70WP at 1g/L or Captan 50WP at 2g/L",
        "dosage": "Apply at petal fall and every 10-14 days through summer. 2-3 sprays during fruit development.",
        "irrigation": "Consistent watering with drip lines. Avoid water stress which weakens tree defences.",
        "soil_correction": "Well-drained loamy soil, pH 6.0-6.5. Annual compost application.",
    },
    "Apple___Cedar_apple_rust": {
        "crop": "Apple",
        "disease": "Cedar Apple Rust",
        "cause": "Fungal infection (Gymnosporangium juniperi-virginianae) — requires both apple and juniper/cedar hosts to complete lifecycle; spores blow from cedar galls to apple during spring rain",
        "severity": "Medium",
        "solution": "Apply myclobutanil or triadimefon fungicide from pink bud through 2nd cover spray. Remove nearby juniper/cedar trees if possible.",
        "prevention": "Plant rust-resistant apple varieties (Freedom, Liberty). Remove all junipers/cedars within 300m radius. Begin fungicide program at pink bud stage.",
        "organic": "Sulfur spray at weekly intervals during spring. Remove cedar galls before they open in spring.",
        "chemical": "Myclobutanil (Rally) 40WP 0.5g/L or Triadimefon (Bayleton) at label rate",
        "dosage": "Start at pink bud stage, repeat every 7-10 days for 4-6 applications",
        "irrigation": "Morning watering only. Drip irrigation preferred. Avoid wetting foliage.",
        "soil_correction": "Well-drained soil. Maintain pH 6.0-7.0. Balanced NPK fertilization.",
    },
    "Apple___healthy": {
        "crop": "Apple",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed. Continue current care regimen.",
        "prevention": "Maintain regular pruning, balanced fertilization (10-10-10 NPK in spring), and preventive fungicide schedule. Monitor for early disease signs.",
        "organic": "Annual compost top-dressing. Dormant oil spray (horticultural oil) in late winter to control overwintering pests.",
        "chemical": "Preventive copper spray at dormant stage if scab pressure exists in area",
        "dosage": "Standard maintenance: balanced fertilizer 200g per tree in spring",
        "irrigation": "1-1.5 inches per week during growing season. Deep watering weekly rather than frequent shallow watering.",
        "soil_correction": "Test soil annually. Apple prefers pH 6.0-7.0. Add sulfur to lower or lime to raise pH.",
    },

    # ═══════════════════════ BLUEBERRY ═══════════════════════════════════
    "Blueberry___healthy": {
        "crop": "Blueberry",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed. Continue regular care.",
        "prevention": "Maintain acidic soil pH 4.5-5.5. Mulch with pine bark or sawdust. Prune old canes annually for vigour.",
        "organic": "Ammonium sulfate fertilizer. Pine needle or acidic compost mulch 5-10cm deep.",
        "chemical": "Preventive sulfur spray if mummy berry is present in area",
        "dosage": "Fertilize with 30-50g ammonium sulfate per plant in early spring",
        "irrigation": "Consistent 1-2 inches/week. Blueberries have shallow roots — drip irrigation prevents drought stress.",
        "soil_correction": "MUST maintain pH 4.5-5.5. Use elemental sulfur to acidify alkaline soil. Add peat moss to planting holes.",
    },

    # ═══════════════════════ CHERRY ══════════════════════════════════════
    "Cherry___Powdery_mildew": {
        "crop": "Cherry",
        "disease": "Powdery Mildew",
        "cause": "Fungal infection (Podosphaera clandestina) — white powdery coating on leaves, develops in warm, dry days with cool, humid nights",
        "severity": "Medium",
        "solution": "Apply sulfur-based fungicide or potassium bicarbonate spray. Remove heavily affected leaves. Improve air circulation through pruning.",
        "prevention": "Plant resistant varieties. Proper pruning for air circulation. Avoid excessive nitrogen which promotes succulent growth.",
        "organic": "Potassium bicarbonate (3g/L) or milk spray (1:9 milk:water). Neem oil every 7-14 days.",
        "chemical": "Myclobutanil 0.5g/L or Trifloxystrobin (Flint) at 0.1g/L",
        "dosage": "Spray every 10-14 days from early infection through harvest. Resume after harvest for fall treatment.",
        "irrigation": "Water at base, avoid overhead sprinklers. Morning watering allows foliage to dry quickly.",
        "soil_correction": "Well-drained loamy soil, pH 6.0-7.0. Avoid excess nitrogen fertilization.",
    },
    "Cherry___healthy": {
        "crop": "Cherry",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Annual pruning for open canopy. Balanced fertilization in early spring. Monitor for cherry leaf spot and brown rot.",
        "organic": "Compost and well-rotted manure application in autumn. Dormant oil spray in late winter.",
        "chemical": "Preventive copper spray at leaf fall and bud swell if disease pressure exists",
        "dosage": "10-10-10 NPK: 100-200g per tree in early spring",
        "irrigation": "Deep watering weekly during dry periods. Reduce watering 2 weeks before harvest for better fruit quality.",
        "soil_correction": "Deep, well-drained soil pH 6.0-7.5. Cherries are sensitive to waterlogging.",
    },

    # ═══════════════════════ CORN ════════════════════════════════════════
    "Corn___Cercospora_leaf_spot Gray_leaf_spot": {
        "crop": "Corn",
        "disease": "Cercospora Leaf Spot (Gray Leaf Spot)",
        "cause": "Fungal infection (Cercospora zeae-maydis) — thrives in warm, humid conditions with heavy dew; survives on corn residue from previous season",
        "severity": "High",
        "solution": "Apply strobilurin fungicide (azoxystrobin) at VT/R1 stage. Rotate away from corn for 1-2 years. Tillage to bury infected residue.",
        "prevention": "Plant resistant hybrids. Rotate with soybean or small grains. Tillage to reduce residue. Avoid late planting.",
        "organic": "Crop rotation (minimum 2 years). Deep moldboard plowing to bury infected residue. Plant earlier for stronger stands.",
        "chemical": "Azoxystrobin (Quadris) at 0.4-0.6L/ha or Pyraclostrobin (Headline) at 0.4L/ha",
        "dosage": "Single application at VT-R1 (tasseling). Apply before disease reaches ear leaf.",
        "irrigation": "Avoid late-evening irrigation that extends leaf wetness. Maintain consistent soil moisture.",
        "soil_correction": "Well-drained fertile soil. Adequate potassium (K) reduces disease severity. pH 5.8-7.0.",
    },
    "Corn___Common_rust": {
        "crop": "Corn",
        "disease": "Common Rust",
        "cause": "Fungal infection (Puccinia sorghi) — airborne spores from southern regions blown north by wind; favoured by cool temperatures (15-25°C) and high humidity",
        "severity": "Medium",
        "solution": "Apply fungicide (triazole or strobilurin) if pustules appear before tasseling. Most hybrids have adequate resistance.",
        "prevention": "Plant resistant hybrids. Early planting to avoid peak spore periods. Scout from V8 onwards.",
        "organic": "Plant resistant varieties. Sulfur-based sprays can slow spread. Ensure good air circulation between rows.",
        "chemical": "Propiconazole (Tilt) 250EC at 0.5L/ha or Azoxystrobin (Quadris) at 0.4L/ha",
        "dosage": "Apply when 1-2 pustules per leaf are found. One application usually sufficient for common rust.",
        "irrigation": "Avoid overhead irrigation. Water early morning to minimize leaf wetness duration.",
        "soil_correction": "Balanced nutrition reduces susceptibility. Ensure adequate phosphorus and potassium.",
    },
    "Corn___Northern_Leaf_Blight": {
        "crop": "Corn",
        "disease": "Northern Leaf Blight",
        "cause": "Fungal infection (Exserohilum turcicum) — long cigar-shaped grey-green lesions; survives on corn debris; favoured by moderate temperatures and heavy dew",
        "severity": "High",
        "solution": "Apply strobilurin or triazole fungicide at first sign of symptoms. Remove and destroy crop debris. Rotate crops.",
        "prevention": "Plant resistant (Ht gene) hybrids. Rotate crops for 2+ years. Tillage to bury residue. Scout from V10 onwards.",
        "organic": "Crop rotation, resistant varieties, deep tillage. Compost increases beneficial soil microbes that suppress pathogen.",
        "chemical": "Azoxystrobin + Propiconazole (Quilt Xcel) at 0.7-1.0L/ha",
        "dosage": "Apply at first symptoms or preventively at VT if disease pressure is high. May need 2 applications 14 days apart.",
        "irrigation": "Avoid late-day irrigation. Maintain adequate row spacing (75cm) for airflow.",
        "soil_correction": "Balanced NPK. Avoid excessive nitrogen which promotes lush growth susceptible to infection.",
    },
    "Corn___healthy": {
        "crop": "Corn",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Scout weekly for rust, blight, and pest damage. Side-dress nitrogen at V6 stage. Maintain weed control.",
        "organic": "Compost side-dressing. Companion planting with beans for nitrogen fixation.",
        "chemical": "Preventive fungicide at VT only if disease pressure is high in area",
        "dosage": "Standard: 150-200 kg/ha nitrogen (split application). 60 kg/ha P₂O₅, 60 kg/ha K₂O at planting.",
        "irrigation": "1-1.5 inches/week during vegetative growth, increasing to 2 inches during tasseling/silking (critical water period).",
        "soil_correction": "pH 5.8-7.0. Deep, well-drained loam. Corn is heavy nitrogen feeder.",
    },

    # ═══════════════════════ GRAPE ═══════════════════════════════════════
    "Grape___Black_rot": {
        "crop": "Grape",
        "disease": "Black Rot",
        "cause": "Fungal infection (Guignardia bidwellii) — causes brown circular lesions on leaves and hard, black mummified berries; spread by rain splash from infected fruit and canes",
        "severity": "High",
        "solution": "Apply myclobutanil or mancozeb fungicide starting at bud break. Remove all mummified fruit and infected canes. Open canopy for airflow.",
        "prevention": "Remove all mummified fruit (primary inoculum source). Prune for open canopy. Begin fungicide program at 3-6 inch shoot growth.",
        "organic": "Bordeaux mixture at dormant stage. Remove all mummified fruit. Copper hydroxide every 10 days from bloom to veraison.",
        "chemical": "Myclobutanil (Rally) 40W at 0.3g/L or Mancozeb 75WP at 2.5g/L",
        "dosage": "Apply at 3-6 inch shoot growth, pre-bloom, post-bloom, and 2 more covers. 5-6 sprays total.",
        "irrigation": "Drip irrigation at base. Avoid wetting fruit clusters. Reduce irrigation before harvest.",
        "soil_correction": "Well-drained soil pH 5.5-6.5. Moderate fertility — excess nitrogen promotes susceptible growth.",
    },
    "Grape___Esca_(Black_Measles)": {
        "crop": "Grape",
        "disease": "Esca (Black Measles)",
        "cause": "Complex fungal infection (Phaeomoniella chlamydospora, Phaeoacremonium spp.) — trunk disease entering through pruning wounds; builds over years before symptoms appear",
        "severity": "High",
        "solution": "No curative treatment exists. Remove severely affected vines. Protect pruning wounds with wound sealant. Retrain new cordons from suckers.",
        "prevention": "Delay pruning to late season (double pruning). Seal large pruning wounds with Trichoderma-based paste. Minimize large cuts.",
        "organic": "Trichoderma-based biological wound protectant. Remove and burn infected wood. Retrain from healthy suckers.",
        "chemical": "No effective chemical cure. Wound protectants: Trichoderma harzianum paste on pruning cuts",
        "dosage": "Apply wound protectant within 24 hours of pruning. Annual Trichoderma trunk treatment.",
        "irrigation": "Maintain consistent moisture — water stress triggers foliar symptoms. Avoid waterlogging.",
        "soil_correction": "Good drainage essential. pH 5.5-7.0. Avoid excessively vigorous rootstocks.",
    },
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "crop": "Grape",
        "disease": "Leaf Blight (Isariopsis Leaf Spot)",
        "cause": "Fungal infection (Pseudocercospora vitis) — angular brown necrotic spots on mature leaves; favoured by warm, humid conditions and poor canopy management",
        "severity": "Medium",
        "solution": "Apply mancozeb or copper-based fungicide. Improve canopy airflow through leaf pulling and shoot positioning.",
        "prevention": "Regular leaf pulling in fruit zone. Position shoots for air circulation. Remove dropped leaves from vineyard floor.",
        "organic": "Copper hydroxide spray every 14 days. Leaf pulling and shoot positioning for airflow.",
        "chemical": "Mancozeb 75WP at 2g/L or Copper oxychloride at 3g/L",
        "dosage": "Apply at first symptoms, repeat every 10-14 days for 3-4 applications",
        "irrigation": "Avoid overhead irrigation. Early morning watering only. Drip irrigation preferred.",
        "soil_correction": "Well-drained soil. Balanced nutrition — avoid excess nitrogen.",
    },
    "Grape___healthy": {
        "crop": "Grape",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Maintain open canopy with proper pruning. Preventive spray program from bud break. Remove all mummified fruit annually.",
        "organic": "Dormant season copper spray. Compost mulch. Balanced organic fertilizer in spring.",
        "chemical": "Preventive sulfur or copper program during growing season",
        "dosage": "Annual: 100-150g balanced vineyard fertilizer per vine in early spring",
        "irrigation": "Consistent 0.5-1 inch/week via drip. Reduce before harvest for sugar concentration.",
        "soil_correction": "pH 5.5-6.5. Good drainage is critical. Annual soil test recommended.",
    },

    # ═══════════════════════ ORANGE ══════════════════════════════════════
    "Orange___Haunglongbing_(Citrus_greening)": {
        "crop": "Orange",
        "disease": "Huanglongbing (Citrus Greening)",
        "cause": "Bacterial infection (Candidatus Liberibacter asiaticus) — transmitted by Asian citrus psyllid (Diaphorina citri); causes mottled yellowing, lopsided fruit, and eventual tree decline",
        "severity": "Critical",
        "solution": "No cure exists. Control psyllid vector aggressively. Remove severely symptomatic trees. Nutritional therapy (enhanced foliar feeding) can extend tree productivity.",
        "prevention": "Control Asian citrus psyllid with systemic insecticides (imidacloprid). Plant certified disease-free nursery stock. Regional psyllid management programs.",
        "organic": "Kaolin clay particle film to deter psyllids. Enhanced nutrition program. Neem oil for psyllid control.",
        "chemical": "Imidacloprid soil drench (0.5g/tree) + Cyfluthrin foliar spray for psyllid. Enhanced micronutrient foliar (Zn, Mn, B, Fe)",
        "dosage": "Psyllid control: Imidacloprid 3-4 times/year. Foliar nutrition monthly during growing season.",
        "irrigation": "Maintain consistent moisture. Microsprinkler irrigation. Avoid water stress which worsens symptoms.",
        "soil_correction": "pH 6.0-7.0. Enhanced fertilization: 150-200% normal rate for HLB-affected trees. Extra zinc and manganese.",
    },

    # ═══════════════════════ PEACH ═══════════════════════════════════════
    "Peach___Bacterial_spot": {
        "crop": "Peach",
        "disease": "Bacterial Spot",
        "cause": "Bacterial infection (Xanthomonas arboricola pv. pruni) — causes small angular lesions on leaves and scabby pitted spots on fruit; spread by wind-driven rain",
        "severity": "Medium",
        "solution": "Apply copper-based bactericide + oxytetracycline during bloom and early fruit development. Select resistant varieties for new plantings.",
        "prevention": "Plant resistant varieties (Contender, Redhaven). Copper spray at leaf fall and bud swell. Avoid overhead irrigation.",
        "organic": "Copper hydroxide at leaf fall and early spring. Avoid excessive nitrogen. Proper pruning for airflow.",
        "chemical": "Copper hydroxide 77WP at 2g/L or Oxytetracycline (Mycoshield) at label rate",
        "dosage": "Copper: 3-4 applications from shuck split through 2nd cover. Oxytetracycline during bloom.",
        "irrigation": "Drip irrigation only. Avoid wetting foliage. Morning watering if overhead is unavoidable.",
        "soil_correction": "Well-drained sandy loam, pH 6.0-6.5. Avoid heavy clay soils.",
    },
    "Peach___healthy": {
        "crop": "Peach",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Dormant copper spray. Annual pruning for open center shape. Monitor for peach leaf curl in spring.",
        "organic": "Dormant oil spray in late winter. Compost application in autumn.",
        "chemical": "Preventive chlorothalonil spray if leaf curl present in area",
        "dosage": "10-10-10 fertilizer: 0.5 kg per tree in early spring before bloom",
        "irrigation": "1-1.5 inches/week during growing season. Reduce 2 weeks before harvest.",
        "soil_correction": "Sandy loam, pH 6.0-6.5. Good drainage crucial — peaches hate wet feet.",
    },

    # ═══════════════════════ PEPPER ══════════════════════════════════════
    "Pepper,_bell___Bacterial_spot": {
        "crop": "Pepper",
        "disease": "Bacterial Spot",
        "cause": "Bacterial infection (Xanthomonas campestris pv. vesicatoria) — causes small dark raised spots on leaves and scabby lesions on fruit; spread by rain splash and contaminated equipment",
        "severity": "High",
        "solution": "Apply copper-based bactericide + mancozeb tank mix. Remove severely infected plants. Use certified disease-free seed.",
        "prevention": "Use certified disease-free seed and transplants. Copper spray program during wet weather. Rotate away from peppers/tomatoes for 2-3 years.",
        "organic": "Copper hydroxide spray every 7-10 days during wet weather. Remove infected leaves promptly.",
        "chemical": "Copper hydroxide 77WP (2g/L) + Mancozeb 75WP (2g/L) tank mix",
        "dosage": "Apply every 7-10 days during rainy season. Start at transplanting.",
        "irrigation": "Drip irrigation mandatory. Overhead water spreads bacteria rapidly. Mulch to prevent soil splash.",
        "soil_correction": "Rich well-drained soil, pH 6.0-6.8. Adequate calcium prevents blossom end rot.",
    },
    "Pepper,_bell___healthy": {
        "crop": "Pepper",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Stake plants for air circulation. Mulch to maintain moisture and prevent soil splash. Monitor for aphids and whiteflies.",
        "organic": "Compost and fish emulsion fertilizer. Companion plant with basil to repel aphids.",
        "chemical": "Preventive copper spray only if bacterial spot present in area",
        "dosage": "Fertilize every 2-3 weeks: 5-10-10 NPK after first fruit set. Calcium foliar spray weekly during fruiting.",
        "irrigation": "1-2 inches/week via drip. Consistent moisture prevents blossom end rot. Mulch 5-8cm deep.",
        "soil_correction": "Warm well-drained soil, pH 6.0-6.8. Add calcium (gypsum) if soil test shows deficiency.",
    },

    # ═══════════════════════ POTATO ══════════════════════════════════════
    "Potato___Early_blight": {
        "crop": "Potato",
        "disease": "Early Blight",
        "cause": "Fungal infection (Alternaria solani) — causes dark concentric ring (target) spots on lower older leaves; favoured by warm temperatures (24-29°C) and alternating wet/dry conditions",
        "severity": "Medium",
        "solution": "Apply chlorothalonil or mancozeb fungicide at first symptoms. Remove infected lower leaves. Maintain adequate nutrition (stressed plants are more susceptible).",
        "prevention": "Plant certified disease-free seed potatoes. Practice 3-year crop rotation. Destroy volunteer potatoes. Adequate fertilization reduces susceptibility.",
        "organic": "Copper-based fungicide every 7-10 days. Mulch to prevent soil splash. Compost for soil health.",
        "chemical": "Chlorothalonil 75WP at 2g/L or Mancozeb 75WP at 2.5g/L",
        "dosage": "Begin at first symptoms or when canopy closes. Repeat every 7-10 days. 5-8 applications per season.",
        "irrigation": "Avoid overhead irrigation. Water early morning. Consistent moisture — drought stress increases susceptibility.",
        "soil_correction": "pH 5.0-6.0 (acidic). Well-drained sandy loam. Adequate potassium reduces disease severity.",
    },
    "Potato___Late_blight": {
        "crop": "Potato",
        "disease": "Late Blight",
        "cause": "Oomycete infection (Phytophthora infestans) — causes dark water-soaked lesions that rapidly kill foliage; spreads explosively in cool, wet weather (10-20°C with >90% humidity)",
        "severity": "Critical",
        "solution": "Apply metalaxyl + mancozeb fungicide IMMEDIATELY. Destroy all infected plant material. Harvest unaffected tubers quickly if foliage is dying.",
        "prevention": "Plant certified seed only. Destroy ALL volunteer potatoes and cull piles. Monitor weather forecasts — spray preventively before rain events during blight weather.",
        "organic": "Copper-based fungicide every 5-7 days during blight weather. Destroy infected plants immediately. Do NOT compost infected material.",
        "chemical": "Metalaxyl (Ridomil Gold) 4g/kg seed treatment + Mancozeb foliar spray (2.5g/L) every 7 days",
        "dosage": "During blight weather: spray every 5-7 days. Ridomil Gold MZ at 2.5g/L. Continue until 2 weeks before harvest.",
        "irrigation": "Avoid any overhead irrigation. Water early morning only. Reduce irrigation frequency during cool wet spells.",
        "soil_correction": "Well-drained soil is critical. Ridge/hill planting to protect tubers. pH 5.0-6.0.",
    },
    "Potato___healthy": {
        "crop": "Potato",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Hill soil around stems as plants grow. Scout weekly for Colorado potato beetle and blight. Use certified seed.",
        "organic": "Compost application before planting. Mulch between rows. Companion plant with horseradish or marigold.",
        "chemical": "Preventive mancozeb spray during known blight conditions",
        "dosage": "Fertilize: 150-200 kg/ha N, 100-150 kg/ha P₂O₅, 150-200 kg/ha K₂O",
        "irrigation": "1-2 inches/week. Critical water periods: tuber initiation and bulking. Reduce before harvest.",
        "soil_correction": "pH 5.0-6.0 (slightly acidic). Well-drained sandy loam. Avoid fresh manure (causes scab).",
    },

    # ═══════════════════════ RASPBERRY ═══════════════════════════════════
    "Raspberry___healthy": {
        "crop": "Raspberry",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Prune fruited canes immediately after harvest. Thin new canes for airflow. Monitor for spotted wing drosophila.",
        "organic": "Compost mulch 5-8cm. Balanced organic fertilizer in spring. Dormant lime sulfur spray.",
        "chemical": "Preventive copper at bud break if cane blight present in area",
        "dosage": "Fertilize: 50-70g 10-10-10 per metre of row in early spring",
        "irrigation": "1-1.5 inches/week via drip. Avoid wetting fruit. Reduce after harvest on summer-bearing types.",
        "soil_correction": "pH 5.5-6.5. Rich, well-drained soil. Raised beds help in heavy clay.",
    },

    # ═══════════════════════ SOYBEAN ═════════════════════════════════════
    "Soybean___healthy": {
        "crop": "Soybean",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Inoculate seed with Bradyrhizobium japonicum for nitrogen fixation. Scout for soybean rust, aphids, and cyst nematode. Rotate with non-legume crops.",
        "organic": "Seed inoculation. Cover crop integration. Compost in low-fertility fields.",
        "chemical": "Preventive fungicide at R3 only if soybean rust present in region",
        "dosage": "Inoculant: follow label rate for seed-applied or in-furrow. Minimal fertilizer needed if well-inoculated.",
        "irrigation": "Critical water need: R1-R5 (flowering through seed fill). 1-1.5 inches/week.",
        "soil_correction": "pH 6.0-7.0. Well-drained fertile soil. Soybean fixes own nitrogen when properly inoculated.",
    },

    # ═══════════════════════ SQUASH ══════════════════════════════════════
    "Squash___Powdery_mildew": {
        "crop": "Squash",
        "disease": "Powdery Mildew",
        "cause": "Fungal infection (Podosphaera xanthii or Erysiphe cichoracearum) — white powdery coating on upper leaf surface; thrives in warm dry days with cool humid nights; does NOT require rain",
        "severity": "Medium",
        "solution": "Apply sulfur or potassium bicarbonate spray. Remove heavily infected leaves. Improve air circulation between plants.",
        "prevention": "Plant resistant varieties (PM-resistant hybrids). Adequate plant spacing (1-1.5m). Avoid excessive nitrogen. Begin spray program at first sign.",
        "organic": "Potassium bicarbonate (3g/L) or milk spray (40% milk solution). Neem oil every 7 days. Sulfur spray in cooler weather.",
        "chemical": "Myclobutanil (Rally) at 0.3g/L or Chlorothalonil 75WP at 2g/L",
        "dosage": "Begin at first white spots. Spray every 7-10 days. Alternate fungicide classes to prevent resistance.",
        "irrigation": "Drip irrigation at base. Morning watering. Avoid wetting foliage.",
        "soil_correction": "Rich well-drained soil, pH 6.0-7.0. Heavy compost application before planting.",
    },

    # ═══════════════════════ STRAWBERRY ══════════════════════════════════
    "Strawberry___Leaf_scorch": {
        "crop": "Strawberry",
        "disease": "Leaf Scorch",
        "cause": "Fungal infection (Diplocarpon earlianum) — causes small dark purple spots that merge into scorched leaf appearance; spread by rain splash; overwinters on infected leaves",
        "severity": "Medium",
        "solution": "Apply captan or myclobutanil fungicide. Remove and destroy infected leaves. Renovate beds after harvest (mow, thin, fertilize).",
        "prevention": "Plant resistant varieties. Proper plant spacing. Remove old leaves and debris annually. Renovate beds after harvest.",
        "organic": "Copper-based spray at renovation. Remove infected leaves. Straw mulch to prevent soil splash.",
        "chemical": "Captan 50WP at 2g/L or Myclobutanil 40WP at 0.3g/L",
        "dosage": "Apply at early bloom and repeat every 10-14 days through harvest. Resume at renovation.",
        "irrigation": "Morning drip irrigation. Avoid overhead watering. Straw mulch to reduce splash.",
        "soil_correction": "pH 5.5-6.5. Well-drained sandy loam. Raised beds in heavy soil areas.",
    },
    "Strawberry___healthy": {
        "crop": "Strawberry",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Renovate beds annually after harvest. Remove runners for bed management. Monitor for spider mites in hot weather.",
        "organic": "Straw mulch for moisture and weed control. Fish emulsion fertilizer every 3 weeks.",
        "chemical": "Preventive captan at bloom if disease pressure exists",
        "dosage": "Balanced fertilizer: 50-75 kg/ha N after renovation. Foliar calcium during fruiting.",
        "irrigation": "1 inch/week via drip. Critical: consistent moisture during fruit development. Reduce before harvest.",
        "soil_correction": "pH 5.5-6.5. Sandy loam with good organic matter. Raised beds preferred.",
    },

    # ═══════════════════════ TOMATO ══════════════════════════════════════
    "Tomato___Bacterial_spot": {
        "crop": "Tomato",
        "disease": "Bacterial Spot",
        "cause": "Bacterial infection (Xanthomonas campestris pv. vesicatoria) — causes small, dark, water-soaked spots on leaves that become raised and scabby on fruit; spread rapidly by rain splash and overhead irrigation",
        "severity": "High",
        "solution": "Apply copper + mancozeb tank mix. Remove heavily spotted leaves. Use certified disease-free transplants for next season.",
        "prevention": "Use certified pathogen-free seed and transplants. Copper spray program during wet weather. Rotate away from solanaceous crops for 2-3 years. Stake and mulch to reduce splash.",
        "organic": "Copper hydroxide 77WP (2g/L) every 5-7 days during wet weather. Remove infected leaves.",
        "chemical": "Copper hydroxide (2g/L) + Mancozeb (2g/L) tank mix",
        "dosage": "Apply at transplanting and every 7-10 days. Intensify to every 5 days during prolonged wet weather.",
        "irrigation": "Only drip irrigation. Never use overhead sprinklers — water splash is the #1 spread method. Mulch heavily.",
        "soil_correction": "Well-drained soil, pH 6.0-6.8. Adequate calcium prevents blossom-end rot.",
    },
    "Tomato___Early_blight": {
        "crop": "Tomato",
        "disease": "Early Blight",
        "cause": "Fungal infection (Alternaria solani) — causes dark concentric ring (target-shaped) spots starting on lower leaves; favoured by warm weather (24-29°C), alternating wet/dry conditions, and stressed plants",
        "severity": "Medium",
        "solution": "Apply chlorothalonil or mancozeb fungicide. Remove infected lower leaves. Mulch to prevent soil splash. Maintain plant vigour with proper nutrition.",
        "prevention": "Stake and mulch plants. Remove lower leaves touching the soil. Practice 3-year rotation. Use disease-free seed. Adequate fertilization reduces susceptibility.",
        "organic": "Copper hydroxide spray every 7-10 days. Compost tea foliar spray. Mulch with straw to prevent soil splash.",
        "chemical": "Chlorothalonil 75WP (2g/L) or Mancozeb 75WP (2.5g/L)",
        "dosage": "Begin at first symptoms on lower leaves. Spray every 7-10 days. 6-8 applications per season.",
        "irrigation": "Drip irrigation. Avoid wetting foliage. Consistent moisture — drought-stressed plants are highly susceptible.",
        "soil_correction": "pH 6.0-6.8. Well-drained soil rich in organic matter. Balanced NPK — avoid nitrogen excess.",
    },
    "Tomato___Late_blight": {
        "crop": "Tomato",
        "disease": "Late Blight",
        "cause": "Oomycete infection (Phytophthora infestans) — causes large dark water-soaked lesions with white fuzzy growth on underside; spreads explosively in cool (10-20°C), wet weather; same pathogen as Irish Potato Famine",
        "severity": "Critical",
        "solution": "Apply metalaxyl + mancozeb IMMEDIATELY. Remove and destroy ALL infected plants (bag and throw away — do NOT compost). Alert neighbouring gardens/farms.",
        "prevention": "Monitor late blight forecasting systems. Plant resistant varieties. Do NOT plant near potatoes. Destroy volunteer tomatoes and potatoes.",
        "organic": "Copper-based fungicide every 5 days during blight weather. DESTROY infected plants immediately — do NOT compost.",
        "chemical": "Metalaxyl (Ridomil Gold MZ) 2.5g/L or Cymoxanil + Mancozeb (Curzate M) 2.5g/L",
        "dosage": "During blight outbreak: spray every 5-7 days. Continue until 2 weeks after last symptoms.",
        "irrigation": "NO overhead irrigation. Drip only. Reduce watering frequency during cool wet weather.",
        "soil_correction": "Well-drained soil. pH 6.0-6.8. Good air circulation between plants (60-90cm spacing).",
    },
    "Tomato___Leaf_Mold": {
        "crop": "Tomato",
        "disease": "Leaf Mold",
        "cause": "Fungal infection (Passalora fulva, syn. Fulvia fulva) — causes pale greenish-yellow spots on upper leaf surface with olive-brown velvety mold on underside; thrives in high humidity (>85%) and warm temperatures in greenhouses",
        "severity": "Medium",
        "solution": "Improve greenhouse ventilation. Reduce humidity below 85%. Apply chlorothalonil fungicide. Space plants for airflow.",
        "prevention": "Ensure greenhouse humidity stays below 85%. Adequate ventilation. Plant resistant varieties. Avoid leaf wetting.",
        "organic": "Improve ventilation and spacing. Baking soda spray (5g/L) or potassium bicarbonate. Remove infected leaves.",
        "chemical": "Chlorothalonil 75WP (2g/L) or Mancozeb 75WP (2g/L)",
        "dosage": "Apply at first symptoms. Repeat every 7-10 days until humidity conditions improve.",
        "irrigation": "Drip only. Increase ventilation. Avoid any water on leaves. Dehumidify greenhouse.",
        "soil_correction": "Well-drained medium. pH 6.0-6.8. Avoid excessive nitrogen in greenhouses.",
    },
    "Tomato___Septoria_leaf_spot": {
        "crop": "Tomato",
        "disease": "Septoria Leaf Spot",
        "cause": "Fungal infection (Septoria lycopersici) — causes numerous small grey-centered spots with dark borders on lower leaves; tiny black dots (pycnidia) visible in spots; favoured by warm wet weather",
        "severity": "Medium",
        "solution": "Apply chlorothalonil or mancozeb fungicide. Remove infected lower leaves. Mulch to prevent rain splash from soil.",
        "prevention": "Stake plants and mulch heavily. Remove lower 30cm of leaves. Rotate away from tomatoes/potatoes for 3 years. Destroy crop residue.",
        "organic": "Copper-based spray every 7-10 days. Remove infected leaves. Heavy straw mulch.",
        "chemical": "Chlorothalonil 75WP (2g/L) or Mancozeb 75WP (2.5g/L)",
        "dosage": "Begin at first symptoms. Spray every 7-10 days until conditions change. Typically 5-7 applications.",
        "irrigation": "Drip irrigation essential. Mulch with straw to prevent soil splash.",
        "soil_correction": "pH 6.0-6.8. Well-drained soil. Destroy all tomato debris at season end.",
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "crop": "Tomato",
        "disease": "Spider Mites (Two-Spotted Spider Mite)",
        "cause": "Pest infestation (Tetranychus urticae) — tiny mites that feed on leaf undersides causing stippled yellow appearance and fine webbing; thrive in hot, dry, dusty conditions",
        "severity": "Medium",
        "solution": "Apply miticide (abamectin or bifenthrin). Spray strong water jet on leaf undersides. Release predatory mites (Phytoseiulus persimilis).",
        "prevention": "Maintain adequate irrigation — drought stress promotes mite outbreaks. Avoid broad-spectrum insecticides that kill mite predators. Dust control on farm roads.",
        "organic": "Neem oil spray (5ml/L) targeting leaf undersides. Release Phytoseiulus persimilis predatory mites. Insecticidal soap spray.",
        "chemical": "Abamectin (Agri-Mek) at 0.5ml/L or Bifenthrin at label rate. Alternate chemicals to prevent resistance.",
        "dosage": "Apply 2-3 times at 7-day intervals, targeting leaf undersides thoroughly. Early morning application preferred.",
        "irrigation": "Increase irrigation — water stress triggers outbreaks. Overhead mist can dislodge mites but risks foliar disease.",
        "soil_correction": "N/A — pest issue, not soil-related. Maintain plant health with balanced nutrition.",
    },
    "Tomato___Target_Spot": {
        "crop": "Tomato",
        "disease": "Target Spot",
        "cause": "Fungal infection (Corynespora cassiicola) — causes brown target-like spots with concentric rings on leaves, stems, and fruit; favoured by warm, humid conditions and overhead irrigation",
        "severity": "Medium",
        "solution": "Apply chlorothalonil or azoxystrobin fungicide. Remove infected leaves. Improve air circulation.",
        "prevention": "Adequate plant spacing. Staking for airflow. Drip irrigation. Early fungicide applications when weather favours disease.",
        "organic": "Copper hydroxide spray every 7-10 days. Remove lower canopy for airflow. Mulch heavily.",
        "chemical": "Chlorothalonil 75WP (2g/L) or Azoxystrobin (Amistar) at 0.5ml/L",
        "dosage": "Begin when spots first appear. Spray every 7-10 days for 4-6 applications.",
        "irrigation": "Drip irrigation only. Avoid overhead water. Water early morning.",
        "soil_correction": "pH 6.0-6.8. Well-drained soil. Destroy crop residues after season.",
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "crop": "Tomato",
        "disease": "Yellow Leaf Curl Virus",
        "cause": "Viral infection (TYLCV) — transmitted by whiteflies (Bemisia tabaci); causes yellowing, upward curling of leaves, and stunted growth; no cure once infected",
        "severity": "Critical",
        "solution": "Remove and destroy infected plants immediately. Control whitefly population aggressively. Use virus-resistant varieties.",
        "prevention": "Plant TYLCV-resistant varieties (Ty gene). Use reflective mulch to repel whiteflies. Fine insect-proof mesh covers. Yellow sticky traps for whitefly monitoring.",
        "organic": "Yellow sticky traps. Reflective silver mulch. Neem oil spray for whitefly control. Remove infected plants immediately.",
        "chemical": "Imidacloprid soil drench at transplanting (0.5g/plant). Cyantraniliprole (Cyazypyr) foliar spray.",
        "dosage": "Imidacloprid drench at transplanting. Follow with foliar spiromesifen every 14 days if whitefly pressure high.",
        "irrigation": "Normal watering. Focus on vector (whitefly) control rather than irrigation changes.",
        "soil_correction": "Standard tomato soil requirements. pH 6.0-6.8. Focus on planting resistant varieties.",
    },
    "Tomato___Tomato_mosaic_virus": {
        "crop": "Tomato",
        "disease": "Mosaic Virus",
        "cause": "Viral infection (ToMV) — causes mottled light/dark green mosaic pattern on leaves, leaf distortion, and reduced yield; extremely stable virus spread by mechanical contact (hands, tools, seed)",
        "severity": "High",
        "solution": "Remove and destroy infected plants. Disinfect hands and tools with 10% bleach or milk solution between plants. Use resistant varieties.",
        "prevention": "Plant TMV/ToMV resistant varieties (Tm-2 gene). Disinfect tools between plants. Do NOT smoke near tomatoes (tobacco mosaic virus). Use certified virus-free seed.",
        "organic": "Strict hygiene — wash hands with milk or 10% skim milk solution. Remove infected plants. Steam-sterilize greenhouse soil.",
        "chemical": "No chemical cure for viral diseases. Focus on prevention and resistant varieties.",
        "dosage": "N/A — no chemical treatment effective. Prevention-only approach.",
        "irrigation": "Normal watering. Virus is not waterborne — spread by contact.",
        "soil_correction": "Standard requirements. pH 6.0-6.8. Soil solarization between crops in greenhouses.",
    },
    "Tomato___healthy": {
        "crop": "Tomato",
        "disease": None,
        "cause": "No disease — plant is healthy",
        "severity": "None",
        "solution": "No treatment needed.",
        "prevention": "Stake and prune for air circulation. Remove lower leaves touching soil. Scout weekly for pests and diseases. Consistent watering to prevent blossom end rot.",
        "organic": "Compost and fish emulsion every 2-3 weeks. Companion plant with basil and marigold.",
        "chemical": "Preventive copper spray only during known disease outbreaks in area",
        "dosage": "Balanced tomato fertilizer (5-10-10) every 2-3 weeks after first fruit set. Calcium foliar spray weekly.",
        "irrigation": "1-2 inches/week via drip irrigation. Consistent moisture — irregular watering causes blossom end rot and cracking.",
        "soil_correction": "pH 6.0-6.8. Rich well-drained soil. Add calcium (gypsum) if blossom end rot occurs.",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# Confidence-based messaging
# ═══════════════════════════════════════════════════════════════════════════
CONFIDENCE_MESSAGES = {
    "very_low": {
        "threshold": 0.3,
        "message": "Image is unclear or not a recognizable crop leaf. Please capture a closer, well-lit photo of a single leaf for accurate diagnosis.",
        "severity_note": "Unable to assess",
    },
    "low": {
        "threshold": 0.6,
        "message": "Image quality or angle makes confident diagnosis difficult. Please capture a closer image of a single leaf for better accuracy.",
        "severity_note": "Needs verification — recommend capturing another image",
    },
    "moderate": {
        "threshold": 0.75,
        "message": "Moderate confidence detection. Results are likely correct but consider verifying with an additional close-up image.",
        "severity_note": "Needs verification",
    },
}


def get_knowledge(class_name: str) -> dict:
    """Get full knowledge entry for a PlantVillage class name.
    
    NEVER returns empty or 'Unknown'. Always returns meaningful agronomic data.
    
    Args:
        class_name: Raw PlantVillage class name, e.g. 'Tomato___Early_blight'
    
    Returns:
        Complete knowledge dict with: crop, disease, cause, severity, solution,
        prevention, organic, chemical, dosage, irrigation, soil_correction.
    """
    # Direct lookup
    if class_name in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[class_name]
    
    # Fuzzy match — handle minor formatting differences
    class_lower = class_name.lower()
    for key, val in KNOWLEDGE_BASE.items():
        if key.lower() == class_lower:
            return val
    
    # Parse class name and try crop-level healthy fallback
    crop, disease = _parse_class(class_name)
    healthy_key = f"{crop}___healthy"
    for key in KNOWLEDGE_BASE:
        if key.lower() == healthy_key.lower():
            entry = dict(KNOWLEDGE_BASE[key])
            if disease:
                entry["disease"] = disease
                entry["cause"] = f"Detected {disease} on {crop}. Specific cause data being compiled — consult local agricultural extension for region-specific guidance."
                entry["severity"] = "Medium"
                entry["solution"] = f"Monitor {crop} closely for {disease} progression. Apply broad-spectrum fungicide (copper-based) as precaution. Remove affected leaves."
            return entry
    
    # Absolute fallback — NEVER return Unknown
    return {
        "crop": crop or "Unidentified Crop",
        "disease": disease,
        "cause": f"Detected signs of {disease or 'health concern'} on plant. Recommend consultation with local agricultural extension service for field-specific diagnosis.",
        "severity": "Medium",
        "solution": "Remove affected leaves. Apply broad-spectrum copper-based fungicide. Improve air circulation and drainage.",
        "prevention": "Practice crop rotation, maintain plant spacing, avoid overhead irrigation, and scout regularly.",
        "organic": "Copper hydroxide spray every 7-10 days. Neem oil for pest issues. Compost tea for general plant health.",
        "chemical": "Broad-spectrum fungicide (mancozeb or chlorothalonil) at label rates",
        "dosage": "Follow product label instructions. Typically 2-3g per litre, every 7-10 days during active symptoms.",
        "irrigation": "Drip irrigation preferred. Avoid wetting foliage. 1-2 inches per week.",
        "soil_correction": "Test soil pH and nutrients. Maintain pH 6.0-7.0 for most crops.",
    }


def validate_crop_disease(crop: str, disease: str | None) -> bool:
    """Two-stage validation: check if disease belongs to this crop.
    
    Returns True if the combination is valid.
    """
    if disease is None:
        return True  # healthy is always valid
    valid = CROP_DISEASE_MAP.get(crop, [])
    if not valid:
        return True  # crop not in map — allow
    return any(d and disease.lower() in d.lower() for d in valid if d)


def get_confidence_message(confidence: float) -> dict | None:
    """Return a warning message if confidence is below threshold.
    
    Returns None if confidence is high enough.
    """
    if confidence < 0.3:
        return CONFIDENCE_MESSAGES["very_low"]
    elif confidence < 0.6:
        return CONFIDENCE_MESSAGES["low"]
    elif confidence < 0.75:
        return CONFIDENCE_MESSAGES["moderate"]
    return None


def _parse_class(class_name: str) -> tuple:
    """Parse PlantVillage class name → (crop, disease) with clean labels."""
    if "___" in class_name:
        parts = class_name.split("___", 1)
        crop = parts[0].replace("_", " ").replace(",", "").strip()
        crop = crop.replace("  ", " ")
        # Normalize crop names
        crop_norm = {
            "Pepper bell": "Pepper",
            "Corn  maize": "Corn",
        }
        crop = crop_norm.get(crop, crop)
        
        disease_raw = parts[1].replace("_", " ").strip()
        if disease_raw.lower() == "healthy":
            return crop, None
        return crop, disease_raw
    return class_name, None
