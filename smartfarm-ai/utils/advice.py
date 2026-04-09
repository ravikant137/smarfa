"""
SmartFarm AI - Offline Advice Engine
Maps detected diseases to actionable, farmer-friendly treatment advice.
Supports multilingual output (English, Hindi, Kannada) with easy expansion.
"""

from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Multilingual advice database
# ---------------------------------------------------------------------------
# Keys must match the class names produced by the PlantVillage dataset
# (or your custom dataset folder names).  Add / edit entries as needed.
#
# Structure:  disease_key -> { lang_code: advice_text }
# ---------------------------------------------------------------------------

DISEASE_ADVICE: Dict[str, Dict[str, str]] = {
    # ── Tomato ──────────────────────────────────────────────────────────
    "Tomato___Bacterial_spot": {
        "en": "Remove and destroy infected leaves. Apply copper-based bactericide spray every 7-10 days. Avoid overhead watering. Rotate crops every 2-3 years.",
        "hi": "संक्रमित पत्तियों को हटाकर नष्ट करें। हर 7-10 दिन में तांबा आधारित जीवाणुनाशक स्प्रे करें। ऊपर से पानी देने से बचें।",
        "kn": "ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತೆಗೆದು ನಾಶಮಾಡಿ. ಪ್ರತಿ 7-10 ದಿನಗಳಿಗೊಮ್ಮೆ ತಾಮ್ರ ಆಧಾರಿತ ಬ್ಯಾಕ್ಟೀರಿಯಾನಾಶಕ ಸಿಂಪಡಿಸಿ.",
    },
    "Tomato___Early_blight": {
        "en": "Apply chlorothalonil or mancozeb fungicide. Remove lower infected leaves. Ensure proper plant spacing for air circulation. Mulch around base of plants.",
        "hi": "क्लोरोथालोनिल या मैंकोजेब फफूंदनाशक लगाएं। नीचे की संक्रमित पत्तियां हटाएं। हवा के संचार के लिए पौधों में उचित दूरी रखें।",
        "kn": "ಕ್ಲೋರೋಥಲೋನಿಲ್ ಅಥವಾ ಮ್ಯಾಂಕೋಜೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಕೆಳಗಿನ ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Tomato___Late_blight": {
        "en": "Apply metalaxyl or mancozeb fungicide immediately. Remove and destroy all infected parts. Avoid wetting leaves when watering. Improve drainage.",
        "hi": "तुरंत मेटालैक्सिल या मैंकोजेब फफूंदनाशक लगाएं। सभी संक्रमित भागों को हटाकर नष्ट करें। पानी देते समय पत्तियों को गीला न करें।",
        "kn": "ತಕ್ಷಣ ಮೆಟಲಾಕ್ಸಿಲ್ ಅಥವಾ ಮ್ಯಾಂಕೋಜೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಎಲ್ಲಾ ಸೋಂಕಿತ ಭಾಗಗಳನ್ನು ತೆಗೆದು ನಾಶಮಾಡಿ.",
    },
    "Tomato___Leaf_Mold": {
        "en": "Improve air circulation in greenhouse. Apply fungicide (chlorothalonil). Remove affected leaves. Reduce humidity below 85%.",
        "hi": "ग्रीनहाउस में हवा का संचार बढ़ाएं। फफूंदनाशक (क्लोरोथालोनिल) लगाएं। प्रभावित पत्तियां हटाएं। नमी 85% से कम रखें।",
        "kn": "ಹಸಿರುಮನೆಯಲ್ಲಿ ಗಾಳಿ ಸಂಚಾರ ಸುಧಾರಿಸಿ. ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಪೀಡಿತ ಎಲೆಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Tomato___Septoria_leaf_spot": {
        "en": "Remove infected leaves immediately. Apply copper fungicide or chlorothalonil. Mulch around plants to prevent soil splash. Water at base of plants only.",
        "hi": "संक्रमित पत्तियों को तुरंत हटाएं। तांबा फफूंदनाशक या क्लोरोथालोनिल लगाएं। मिट्टी के छींटे रोकने के लिए पौधों के चारों ओर मल्च करें।",
        "kn": "ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತಕ್ಷಣ ತೆಗೆಯಿರಿ. ತಾಮ್ರ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "en": "Spray neem oil or insecticidal soap. Increase humidity around plants. Introduce predatory mites as biological control. Avoid dusty conditions.",
        "hi": "नीम का तेल या कीटनाशक साबुन स्प्रे करें। पौधों के आसपास नमी बढ़ाएं। जैविक नियंत्रण के लिए शिकारी कीटों का उपयोग करें।",
        "kn": "ಬೇವಿನ ಎಣ್ಣೆ ಅಥವಾ ಕೀಟನಾಶಕ ಸೋಪ್ ಸಿಂಪಡಿಸಿ. ಸಸ್ಯಗಳ ಸುತ್ತ ಆರ್ದ್ರತೆ ಹೆಚ್ಚಿಸಿ.",
    },
    "Tomato___Target_Spot": {
        "en": "Apply chlorothalonil or mancozeb fungicide. Remove infected leaves. Improve air circulation. Avoid overhead irrigation.",
        "hi": "क्लोरोथालोनिल या मैंकोजेब फफूंदनाशक लगाएं। संक्रमित पत्तियां हटाएं। हवा का संचार सुधारें।",
        "kn": "ಕ್ಲೋರೋಥಲೋನಿಲ್ ಅಥವಾ ಮ್ಯಾಂಕೋಜೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "en": "Control whiteflies using yellow sticky traps and neem oil. Remove infected plants immediately. Use virus-resistant varieties. Cover nurseries with fine mesh.",
        "hi": "पीले चिपचिपे जाल और नीम के तेल से सफेद मक्खियों को नियंत्रित करें। संक्रमित पौधों को तुरंत हटाएं। वायरस प्रतिरोधी किस्मों का उपयोग करें।",
        "kn": "ಹಳದಿ ಅಂಟು ಬಲೆಗಳು ಮತ್ತು ಬೇವಿನ ಎಣ್ಣೆ ಬಳಸಿ ಬಿಳಿನೊಣಗಳನ್ನು ನಿಯಂತ್ರಿಸಿ. ಸೋಂಕಿತ ಸಸ್ಯಗಳನ್ನು ತಕ್ಷಣ ತೆಗೆಯಿರಿ.",
    },
    "Tomato___Tomato_mosaic_virus": {
        "en": "Remove and destroy infected plants. Disinfect tools with 10% bleach solution. Wash hands before handling plants. Use resistant seed varieties.",
        "hi": "संक्रमित पौधों को हटाकर नष्ट करें। 10% ब्लीच घोल से उपकरण कीटाणुरहित करें। पौधों को छूने से पहले हाथ धोएं।",
        "kn": "ಸೋಂಕಿತ ಸಸ್ಯಗಳನ್ನು ತೆಗೆದು ನಾಶಮಾಡಿ. 10% ಬ್ಲೀಚ್ ದ್ರಾವಣದಿಂದ ಉಪಕರಣಗಳನ್ನು ಸೋಂಕುರಹಿತಗೊಳಿಸಿ.",
    },
    "Tomato___healthy": {
        "en": "Your tomato plant looks healthy! Continue regular watering, balanced fertilization, and monitor for early signs of disease.",
        "hi": "आपका टमाटर का पौधा स्वस्थ दिखता है! नियमित पानी देना जारी रखें और बीमारी के शुरुआती लक्षणों पर नजर रखें।",
        "kn": "ನಿಮ್ಮ ಟೊಮ್ಯಾಟೋ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿ ಕಾಣುತ್ತಿದೆ! ನಿಯಮಿತ ನೀರಾವರಿ ಮುಂದುವರಿಸಿ.",
    },

    # ── Potato ───────────────────────────────────────────────────────────
    "Potato___Early_blight": {
        "en": "Apply mancozeb or chlorothalonil fungicide. Remove infected lower leaves. Ensure adequate plant spacing. Hill potatoes to protect tubers.",
        "hi": "मैंकोजेब या क्लोरोथालोनिल फफूंदनाशक लगाएं। संक्रमित निचली पत्तियां हटाएं। पर्याप्त पौधों की दूरी सुनिश्चित करें।",
        "kn": "ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ಕ್ಲೋರೋಥಲೋನಿಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಸೋಂಕಿತ ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Potato___Late_blight": {
        "en": "Apply metalaxyl-mancozeb fungicide. Destroy all infected plant material. Do not compost infected debris. Ensure good field drainage.",
        "hi": "मेटालैक्सिल-मैंकोजेब फफूंदनाशक लगाएं। सभी संक्रमित पौधे सामग्री नष्ट करें। संक्रमित अवशेषों को खाद न बनाएं।",
        "kn": "ಮೆಟಲಾಕ್ಸಿಲ್-ಮ್ಯಾಂಕೋಜೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಎಲ್ಲಾ ಸೋಂಕಿತ ಸಸ್ಯ ವಸ್ತುಗಳನ್ನು ನಾಶಮಾಡಿ.",
    },
    "Potato___healthy": {
        "en": "Your potato plant is healthy! Maintain consistent watering and watch for signs of blight during wet weather.",
        "hi": "आपका आलू का पौधा स्वस्थ है! लगातार पानी दें और गीले मौसम में ब्लाइट के लक्षणों पर नजर रखें।",
        "kn": "ನಿಮ್ಮ ಆಲೂಗಡ್ಡೆ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ! ಸ್ಥಿರ ನೀರಾವರಿ ಮುಂದುವರಿಸಿ.",
    },

    # ── Corn (Maize) ────────────────────────────────────────────────────
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "en": "Apply strobilurin or triazole fungicide. Rotate crops with non-host plants. Plow under crop residues after harvest. Use resistant hybrids.",
        "hi": "स्ट्रोबिलुरिन या ट्राइज़ोल फफूंदनाशक लगाएं। गैर-मेज़बान पौधों के साथ फसल चक्र अपनाएं।",
        "kn": "ಸ್ಟ್ರೋಬಿಲ್ಯೂರಿನ್ ಅಥವಾ ಟ್ರಯಾಜೋಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಅತಿಥೇಯವಲ್ಲದ ಸಸ್ಯಗಳೊಂದಿಗೆ ಬೆಳೆ ಸರದಿ ಮಾಡಿ.",
    },
    "Corn_(maize)___Common_rust_": {
        "en": "Apply mancozeb or triazole fungicide at first sign of rust. Plant resistant varieties. Monitor regularly during warm, humid weather.",
        "hi": "रस्ट के पहले लक्षण पर मैंकोजेब या ट्राइज़ोल फफूंदनाशक लगाएं। प्रतिरोधी किस्में लगाएं।",
        "kn": "ತುಕ್ಕಿನ ಮೊದಲ ಚಿಹ್ನೆಯಲ್ಲಿ ಮ್ಯಾಂಕೋಜೆಬ್ ಅಥವಾ ಟ್ರಯಾಜೋಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Corn_(maize)___Northern_Leaf_Blight": {
        "en": "Apply propiconazole or azoxystrobin fungicide. Remove crop residue after harvest. Use resistant hybrids. Practice crop rotation.",
        "hi": "प्रोपिकोनाज़ोल या एज़ोक्सिस्ट्रोबिन फफूंदनाशक लगाएं। कटाई के बाद फसल अवशेष हटाएं।",
        "kn": "ಪ್ರೊಪಿಕೊನಾಜೋಲ್ ಅಥವಾ ಅಜೊಕ್ಸಿಸ್ಟ್ರೋಬಿನ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಕೊಯ್ಲಿನ ನಂತರ ಬೆಳೆ ಅವಶೇಷಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Corn_(maize)___healthy": {
        "en": "Your corn plant is healthy! Ensure proper nitrogen fertilization and maintain consistent soil moisture.",
        "hi": "आपका मक्का का पौधा स्वस्थ है! उचित नाइट्रोजन उर्वरक दें और मिट्टी में नमी बनाए रखें।",
        "kn": "ನಿಮ್ಮ ಜೋಳದ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ! ಸರಿಯಾದ ಸಾರಜನಕ ಗೊಬ್ಬರ ಒದಗಿಸಿ.",
    },

    # ── Apple ────────────────────────────────────────────────────────────
    "Apple___Apple_scab": {
        "en": "Apply captan or myclobutanil fungicide in spring. Rake and destroy fallen leaves in autumn. Prune trees to improve air circulation.",
        "hi": "वसंत में कैप्टन या माइक्लोब्यूटानिल फफूंदनाशक लगाएं। शरद ऋतु में गिरी पत्तियां इकट्ठा करके नष्ट करें।",
        "kn": "ವಸಂತದಲ್ಲಿ ಕ್ಯಾಪ್ಟನ್ ಅಥವಾ ಮೈಕ್ಲೋಬ್ಯೂಟನಿಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Apple___Black_rot": {
        "en": "Prune out dead or infected branches. Apply captan fungicide during growing season. Remove mummified fruits. Keep tree healthy with proper fertilization.",
        "hi": "मृत या संक्रमित शाखाएं काटें। बढ़ते मौसम में कैप्टन फफूंदनाशक लगाएं। ममीफाइड फल हटाएं।",
        "kn": "ಸತ್ತ ಅಥವಾ ಸೋಂಕಿತ ಕೊಂಬೆಗಳನ್ನು ಕತ್ತರಿಸಿ. ಬೆಳೆಯುವ ಋತುವಿನಲ್ಲಿ ಕ್ಯಾಪ್ಟನ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Apple___Cedar_apple_rust": {
        "en": "Apply myclobutanil fungicide in spring. Remove nearby cedar/juniper trees if possible. Use resistant apple varieties.",
        "hi": "वसंत में माइक्लोब्यूटानिल फफूंदनाशक लगाएं। यदि संभव हो तो आसपास के देवदार/जुनिपर पेड़ हटाएं।",
        "kn": "ವಸಂತದಲ್ಲಿ ಮೈಕ್ಲೋಬ್ಯೂಟನಿಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Apple___healthy": {
        "en": "Your apple tree looks healthy! Continue regular pruning and balanced fertilization.",
        "hi": "आपका सेब का पेड़ स्वस्थ दिखता है! नियमित छंटाई और संतुलित उर्वरक जारी रखें।",
        "kn": "ನಿಮ್ಮ ಸೇಬಿನ ಮರ ಆರೋಗ್ಯಕರವಾಗಿ ಕಾಣುತ್ತಿದೆ!",
    },

    # ── Grape ────────────────────────────────────────────────────────────
    "Grape___Black_rot": {
        "en": "Apply myclobutanil or mancozeb fungicide before bloom. Remove mummified berries and infected leaves. Ensure good canopy management.",
        "hi": "फूल आने से पहले माइक्लोब्यूटानिल या मैंकोजेब फफूंदनाशक लगाएं। ममीफाइड बेर और संक्रमित पत्तियां हटाएं।",
        "kn": "ಹೂ ಬರುವ ಮೊದಲು ಮೈಕ್ಲೋಬ್ಯೂಟನಿಲ್ ಅಥವಾ ಮ್ಯಾಂಕೋಜೆಬ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Grape___Esca_(Black_Measles)": {
        "en": "No effective chemical treatment exists. Remove and destroy severely infected vines. Minimize pruning wounds. Apply wound sealant after pruning.",
        "hi": "कोई प्रभावी रासायनिक उपचार नहीं है। गंभीर रूप से संक्रमित बेलों को हटाकर नष्ट करें।",
        "kn": "ಯಾವುದೇ ಪರಿಣಾಮಕಾರಿ ರಾಸಾಯನಿಕ ಚಿಕಿತ್ಸೆ ಇಲ್ಲ. ತೀವ್ರವಾಗಿ ಸೋಂಕಿತ ಬಳ್ಳಿಗಳನ್ನು ತೆಗೆದು ನಾಶಮಾಡಿ.",
    },
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "en": "Apply copper-based fungicide. Remove infected leaves. Improve air circulation through canopy management. Avoid excessive nitrogen.",
        "hi": "तांबा आधारित फफूंदनाशक लगाएं। संक्रमित पत्तियां हटाएं। छत्र प्रबंधन से हवा का संचार सुधारें।",
        "kn": "ತಾಮ್ರ ಆಧಾರಿತ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ. ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Grape___healthy": {
        "en": "Your grapevine is healthy! Maintain good canopy management and monitor during humid conditions.",
        "hi": "आपकी अंगूर की बेल स्वस्थ है! अच्छा छत्र प्रबंधन बनाए रखें।",
        "kn": "ನಿಮ್ಮ ದ್ರಾಕ್ಷಿ ಬಳ್ಳಿ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },

    # ── Pepper ───────────────────────────────────────────────────────────
    "Pepper,_bell___Bacterial_spot": {
        "en": "Apply copper-based bactericide. Remove infected plant parts. Use disease-free seeds. Avoid overhead irrigation. Rotate crops every 2-3 years.",
        "hi": "तांबा आधारित जीवाणुनाशक लगाएं। संक्रमित पौधे के हिस्से हटाएं। रोगमुक्त बीजों का उपयोग करें।",
        "kn": "ತಾಮ್ರ ಆಧಾರಿತ ಬ್ಯಾಕ್ಟೀರಿಯಾನಾಶಕ ಹಚ್ಚಿ. ಸೋಂಕಿತ ಸಸ್ಯ ಭಾಗಗಳನ್ನು ತೆಗೆಯಿರಿ.",
    },
    "Pepper,_bell___healthy": {
        "en": "Your pepper plant is healthy! Keep up regular watering and balanced nutrition.",
        "hi": "आपका शिमला मिर्च का पौधा स्वस्थ है! नियमित पानी और संतुलित पोषण जारी रखें।",
        "kn": "ನಿಮ್ಮ ದೊಣ್ಣೆ ಮೆಣಸಿನ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },

    # ── Strawberry ──────────────────────────────────────────────────────
    "Strawberry___Leaf_scorch": {
        "en": "Remove infected leaves. Apply copper fungicide. Ensure good air circulation. Avoid excessive nitrogen fertilization.",
        "hi": "संक्रमित पत्तियां हटाएं। तांबा फफूंदनाशक लगाएं। अच्छा हवा संचार सुनिश्चित करें।",
        "kn": "ಸೋಂಕಿತ ಎಲೆಗಳನ್ನು ತೆಗೆಯಿರಿ. ತಾಮ್ರ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Strawberry___healthy": {
        "en": "Your strawberry plant is healthy! Maintain raised beds and proper mulching.",
        "hi": "आपका स्ट्रॉबेरी का पौधा स्वस्थ है! उचित मल्चिंग बनाए रखें।",
        "kn": "ನಿಮ್ಮ ಸ್ಟ್ರಾಬೆರಿ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },

    # ── Peach ────────────────────────────────────────────────────────────
    "Peach___Bacterial_spot": {
        "en": "Apply oxytetracycline or copper sprays. Plant resistant varieties. Avoid overhead irrigation. Prune to improve air circulation.",
        "hi": "ऑक्सीटेट्रासाइक्लिन या तांबा स्प्रे लगाएं। प्रतिरोधी किस्में लगाएं।",
        "kn": "ಆಕ್ಸಿಟೆಟ್ರಾಸೈಕ್ಲಿನ್ ಅಥವಾ ತಾಮ್ರ ಸಿಂಪಡಣೆ ಹಚ್ಚಿ.",
    },
    "Peach___healthy": {
        "en": "Your peach tree is healthy! Maintain regular pruning and adequate water supply.",
        "hi": "आपका आड़ू का पेड़ स्वस्थ है! नियमित छंटाई और पर्याप्त पानी की आपूर्ति बनाए रखें।",
        "kn": "ನಿಮ್ಮ ಪೀಚ್ ಮರ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },

    # ── Cherry ──────────────────────────────────────────────────────────
    "Cherry_(including_sour)___Powdery_mildew": {
        "en": "Apply sulfur or myclobutanil fungicide. Prune for air circulation. Remove infected shoots. Water at soil level.",
        "hi": "सल्फर या माइक्लोब्यूटानिल फफूंदनाशक लगाएं। हवा के संचार के लिए छंटाई करें।",
        "kn": "ಸಲ್ಫರ್ ಅಥವಾ ಮೈಕ್ಲೋಬ್ಯೂಟನಿಲ್ ಶಿಲೀಂಧ್ರನಾಶಕ ಹಚ್ಚಿ.",
    },
    "Cherry_(including_sour)___healthy": {
        "en": "Your cherry tree is healthy! Maintain proper pruning schedule.",
        "hi": "आपका चेरी का पेड़ स्वस्थ है!",
        "kn": "ನಿಮ್ಮ ಚೆರ್ರಿ ಮರ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },

    # ── Soybean ─────────────────────────────────────────────────────────
    "Soybean___healthy": {
        "en": "Your soybean plant is healthy! Continue proper crop management and pest monitoring.",
        "hi": "आपका सोयाबीन का पौधा स्वस्थ है!",
        "kn": "ನಿಮ್ಮ ಸೋಯಾಬೀನ್ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },

    # ── Squash ──────────────────────────────────────────────────────────
    "Squash___Powdery_mildew": {
        "en": "Apply sulfur or potassium bicarbonate. Improve air circulation. Water at base of plants. Remove severely infected leaves.",
        "hi": "सल्फर या पोटैशियम बाइकार्बोनेट लगाएं। हवा का संचार सुधारें। पौधों के आधार पर पानी दें।",
        "kn": "ಸಲ್ಫರ್ ಅಥವಾ ಪೊಟ್ಯಾಸಿಯಂ ಬೈಕಾರ್ಬೊನೇಟ್ ಹಚ್ಚಿ.",
    },

    # ── Orange ──────────────────────────────────────────────────────────
    "Orange___Haunglongbing_(Citrus_greening)": {
        "en": "No cure exists. Control Asian citrus psyllid with insecticides. Remove infected trees to prevent spread. Plant certified disease-free nursery stock.",
        "hi": "कोई इलाज नहीं है। कीटनाशकों से एशियन सिट्रस सिल्लिड को नियंत्रित करें। प्रसार रोकने के लिए संक्रमित पेड़ हटाएं।",
        "kn": "ಯಾವುದೇ ಚಿಕಿತ್ಸೆ ಇಲ್ಲ. ಕೀಟನಾಶಕಗಳಿಂದ ಏಷ್ಯನ್ ಸಿಟ್ರಸ್ ಸಿಲ್ಲಿಡ್ ನಿಯಂತ್ರಿಸಿ.",
    },

    # ── Raspberry ───────────────────────────────────────────────────────
    "Raspberry___healthy": {
        "en": "Your raspberry plant is healthy! Maintain good air circulation and proper cane management.",
        "hi": "आपका रास्पबेरी का पौधा स्वस्थ है!",
        "kn": "ನಿಮ್ಮ ರಾಸ್ಪ್‌ಬೆರಿ ಗಿಡ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
    },
}

# Supported languages
SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi", "kn": "Kannada"}


# ---------------------------------------------------------------------------
# Advice lookup
# ---------------------------------------------------------------------------
def get_advice(disease_name: str, lang: str = "en") -> str:
    """Return treatment advice for the given disease in the requested language.

    Falls back to English if the requested language is unavailable,
    and returns a generic message if the disease is not in the database.
    """
    lang = lang if lang in SUPPORTED_LANGUAGES else "en"

    advice_entry = DISEASE_ADVICE.get(disease_name)

    if advice_entry is None:
        # Try fuzzy match (case-insensitive, ignoring underscores/spaces)
        normalized = disease_name.lower().replace(" ", "_")
        for key, val in DISEASE_ADVICE.items():
            if key.lower().replace(" ", "_") == normalized:
                advice_entry = val
                break

    if advice_entry is None:
        fallback = {
            "en": f"Disease '{disease_name}' detected. Please consult your local agricultural extension officer for specific treatment advice.",
            "hi": f"रोग '{disease_name}' का पता चला। कृपया विशिष्ट उपचार सलाह के लिए अपने स्थानीय कृषि अधिकारी से संपर्क करें।",
            "kn": f"ರೋಗ '{disease_name}' ಪತ್ತೆಯಾಗಿದೆ. ನಿರ್ದಿಷ್ಟ ಚಿಕಿತ್ಸೆ ಸಲಹೆಗಾಗಿ ನಿಮ್ಮ ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        }
        return fallback.get(lang, fallback["en"])

    return advice_entry.get(lang, advice_entry.get("en", "No advice available."))


def get_all_diseases() -> list:
    """Return a sorted list of all known disease names."""
    return sorted(DISEASE_ADVICE.keys())


def get_supported_languages() -> Dict[str, str]:
    """Return the supported language map."""
    return SUPPORTED_LANGUAGES.copy()
