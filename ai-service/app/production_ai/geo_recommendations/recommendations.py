"""
Multilingual Recommendations Catalogue and Conversational KissanGPT-style AI Agronomist Layer
"""

from typing import Dict, Any, List

LOCALIZED_CATALOGUE = {
    "kannada": {
        "disease_label": "ರೋಗ ಪತ್ತೆಯಾಗಿದೆ",
        "organic_title": "ಸಾವಯವ ಪರಿಹಾರ",
        "chemical_title": "ರಾಸಾಯನಿಕ ನಿಯಂತ್ರಣ",
        "soil_title": "ಮಣ್ಣಿನ ಆರೈಕೆ",
        "organic_Tomato___Late_blight": "ಕೊಳವೆ ರೋಗಕ್ಕೆ ತಾಮ್ರದ ಬೋರ್ಡೋ ದ್ರಾವಣವನ್ನು ಸಿಂಪಡಿಸಿ. ಕೊಳೆತ ಎಲೆಗಳನ್ನು ನಾಶಪಡಿಸಿ.",
        "chemical_Tomato___Late_blight": "ಮೆಟಾಲಾಕ್ಸಿಲ್ + ಮ್ಯಾಂಕೋಜೆಬ್ 2.5 ಗ್ರಾಂ/ಲೀಟರ್ ನೀರಿನಲ್ಲಿ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ.",
        "prevention_Tomato___Late_blight": "ಗಿಡಗಳ ಮಧ್ಯೆ ಗಾಳಿ ಸಂಚಾರಕ್ಕೆ ಜಾಗ ಬಿಡಿ. ಆಕಾಶ ನೀರಾವರಿ ಪದ್ಧತಿ ತಪ್ಪಿಸಿ.",
    },
    "hindi": {
        "disease_label": "बीमारी का पता चला",
        "organic_title": "जैविक उपचार",
        "chemical_title": "रासायनिक उपचार",
        "soil_title": "मिट्टी की देखभाल",
        "organic_Tomato___Late_blight": "तांबे के बोर्डो मिश्रण का छिड़काव करें। संक्रमित पौधों को तुरंत नष्ट करें।",
        "chemical_Tomato___Late_blight": "मेटालैक्सिल + मैन्कोजेब 2.5 ग्राम प्रति लीटर पानी में मिलाकर छिड़काव करें।",
        "prevention_Tomato___Late_blight": "पौधों के बीच हवा के आवागमन को बनाए रखें। टपकन सिंचाई प्रणाली अपनाएं।",
    },
    "marathi": {
        "disease_label": "रोगाचे निदान झाले",
        "organic_title": "सेंद्रिय उपाय",
        "chemical_title": "रासायनिक नियंत्रण",
        "soil_title": "माती व्यवस्थापन",
        "organic_Tomato___Late_blight": "तांब्याचे बोर्डो मिश्रण फवारावे. रोगट झाडे काढून नष्ट करावीत.",
        "chemical_Tomato___Late_blight": "मेटालॅक्सिल + मँकोझेब २.೫ ग्रॅम प्रति लिटर पाण्यात मिसळून फवारणी करा.",
        "prevention_Tomato___Late_blight": "हवा खेळती राहील अशी झाडांची लागवड करावी. तुषार सिंचन टाळावे.",
    },
    "english": {
        "disease_label": "Disease Detected",
        "organic_title": "Organic Treatment",
        "chemical_title": "Chemical Control",
        "soil_title": "Soil Management",
        "organic_Tomato___Late_blight": "Apply organic copper-based fungicide every 5 days during wet weather. Remove all infected leaves immediately.",
        "chemical_Tomato___Late_blight": "Apply Metalaxyl (Ridomil Gold) 2.5g/L or Cymoxanil + Mancozeb (Curzate) 2.5g/L immediately.",
        "prevention_Tomato___Late_blight": "Ensure good spacing between plants. Avoid overhead watering.",
    }
}

class AgriculturalGPTLayer:
    def __init__(self):
        """KissanGPT-style AI agent to answer queries in local dialects."""
        pass

    def generate_kissan_response(
        self, 
        crop: str, 
        disease: str, 
        language: str, 
        farmer_query: str
    ) -> str:
        """Dynamic conversational agronomy layer fallback."""
        lang = language.lower()
        if "tomato" in crop.lower() and "blight" in disease.lower():
            if lang == "kannada":
                return f"ಟೊಮೆಟೊ ಕೊಳೆ ರೋಗದ ಕುರಿತು ಪ್ರಶ್ನೆಗೆ ಧನ್ಯವಾದಗಳು. '{farmer_query}' ಗೆ ಉತ್ತರವೇನೆಂದರೆ: ತಾಮ್ರಯುಕ್ತ ಔಷಧಿಗಳನ್ನು ಸಿಂಪಡಿಸಿರಿ ಮತ್ತು ಹಾನಿಗೊಳಗಾದ ಎಲೆಗಳನ್ನು ಕೂಡಲೇ ತೋಟದಿಂದ ದೂರವಿಡಿ."
            elif lang == "hindi":
                return f"टमाटर झुलसा रोग के बारे में आपके सवाल के लिए धन्यवाद। '{farmer_query}' का उत्तर यह है: जैविक तांबा कवकनाशी का प्रयोग करें और संक्रमित पत्तियों को नष्ट कर दें।"
            elif lang == "marathi":
                return f"टोमॅटो करपा रोगाबद्दल विचारलेल्या प्रश्नाचे उत्तर खालीलप्रमाणे आहे: तांबायुक्त बुरशीनाशकांची त्वरित फवारणी करा आणि बाधीत पाने शेताबाहेर नेऊन जाळा."
            else:
                return f"Thank you for asking about {crop} {disease}. In response to '{farmer_query}': We highly recommend applying copper-based controls, pruning crowded branches for air ventilation, and moving to drip irrigation."

        # General Fallback
        if lang == "kannada":
            return "ನಮಸ್ಕಾರ, ನಿಮ್ಮ ಬೆಳೆಯ ಆರೋಗ್ಯ ಕಾಪಾಡಲು ನೀರಾವರಿಯನ್ನು ವ್ಯವಸ್ಥಿತವಾಗಿ ನಿರ್ವಹಿಸಿ ಮತ್ತು ಉತ್ತಮ ಮಣ್ಣಿನ ಫಲವತ್ತತೆ ಕಾಪಾಡಿಕೊಳ್ಳಿ."
        elif lang == "hindi":
            return "नमस्कार, फसल की सुरक्षा के लिए पानी का संतुलन बनाए रखें और उचित जैविक खाद का प्रयोग करें।"
        elif lang == "marathi":
            return "नमस्कार, पिकाच्या चांगल्या वाढीसाठी पाणी योग्य प्रमाणात द्या आणि सेंद्रिय खतांचा वापर करा."
        else:
            return "Hello, to preserve plant health, ensure consistent drip watering, check soil nitrogen levels, and maintain proper drainage."
