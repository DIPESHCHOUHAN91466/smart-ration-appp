"""Localized explanation text for AI outputs (en / hi / mr).

Every reason is returned as a stable `code` plus `params` AND a rendered
`text` in the requested language, so the frontend can either show the text or
translate the code itself. Unknown languages fall back to English.
"""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    # Forecasting
    "FORECAST_INSUFFICIENT_DATA": {
        "en": "Insufficient historical data for reliable forecasting ({days} of {required} days available).",
        "hi": "विश्वसनीय पूर्वानुमान के लिए पर्याप्त ऐतिहासिक डेटा नहीं है ({required} में से {days} दिन उपलब्ध)।",
        "mr": "विश्वसनीय अंदाजासाठी पुरेसा ऐतिहासिक डेटा नाही ({required} पैकी {days} दिवस उपलब्ध).",
    },
    "FORECAST_METHOD": {
        "en": "Based on {days} days of distribution history using {method}.",
        "hi": "{days} दिनों के वितरण इतिहास पर आधारित ({method})।",
        "mr": "{days} दिवसांच्या वितरण इतिहासावर आधारित ({method}).",
    },
    # Inventory
    "STOCK_OUT": {"en": "Out of stock.", "hi": "स्टॉक समाप्त।", "mr": "साठा संपला."},
    "STOCK_CRITICAL": {
        "en": "Only ~{days} days of stock left at current usage.",
        "hi": "वर्तमान खपत पर केवल ~{days} दिन का स्टॉक बचा है।",
        "mr": "सध्याच्या वापरानुसार फक्त ~{days} दिवसांचा साठा शिल्लक.",
    },
    "STOCK_BELOW_REORDER": {
        "en": "Stock {stock} is at or below the reorder level {level}.",
        "hi": "स्टॉक {stock} पुनः ऑर्डर स्तर {level} पर या उससे कम है।",
        "mr": "साठा {stock} पुनर्मागणी पातळी {level} इतका किंवा कमी आहे.",
    },
    "STOCK_LOW_DAYS": {
        "en": "About {days} days of stock left — reorder soon.",
        "hi": "लगभग {days} दिन का स्टॉक बचा है — जल्द ऑर्डर करें।",
        "mr": "सुमारे {days} दिवसांचा साठा शिल्लक — लवकर मागणी करा.",
    },
    "STOCK_RESERVED_EXCEEDS": {
        "en": "Booked tokens reserve {reserved}, more than the {stock} in stock.",
        "hi": "बुक किए गए टोकन {reserved} आरक्षित करते हैं, जो स्टॉक {stock} से अधिक है।",
        "mr": "बुक केलेल्या टोकनसाठी {reserved} राखीव, साठ्यातील {stock} पेक्षा जास्त.",
    },
    "STOCK_NO_USAGE": {
        "en": "No distribution recorded in the analysis window.",
        "hi": "विश्लेषण अवधि में कोई वितरण दर्ज नहीं हुआ।",
        "mr": "विश्लेषण कालावधीत कोणतेही वितरण नोंदलेले नाही.",
    },
    # Risk
    "RISK_TOKEN_REUSE": {
        "en": "{count} attempt(s) to reuse an already-collected token.",
        "hi": "पहले से उपयोग किए गए टोकन के {count} पुनः उपयोग प्रयास।",
        "mr": "आधीच वापरलेले टोकन पुन्हा वापरण्याचे {count} प्रयत्न.",
    },
    "RISK_BLOCKED_VERIFICATION": {
        "en": "{count} blocked verification(s).",
        "hi": "{count} अवरुद्ध सत्यापन।",
        "mr": "{count} अवरोधित पडताळण्या.",
    },
    "RISK_COLLECTION_REJECTED": {
        "en": "{count} rejected collection attempt(s).",
        "hi": "{count} अस्वीकृत संग्रह प्रयास।",
        "mr": "{count} नाकारलेले संकलन प्रयत्न.",
    },
    "RISK_RAPID_CLAIMS": {
        "en": "{count} collections within 24 hours of a previous one.",
        "hi": "पिछले संग्रह के 24 घंटे के भीतर {count} संग्रह।",
        "mr": "मागील संकलनानंतर 24 तासांत {count} संकलने.",
    },
    "RISK_OVER_ENTITLEMENT": {
        "en": "Collected {collected} {item} this month, above the {entitled} entitlement.",
        "hi": "इस महीने {collected} {item} लिया गया, जो {entitled} पात्रता से अधिक है।",
        "mr": "या महिन्यात {collected} {item} घेतले, {entitled} पात्रतेपेक्षा जास्त.",
    },
    "RISK_OTHER_SHOP": {
        "en": "{count} collection(s) at a shop other than the assigned shop.",
        "hi": "निर्धारित दुकान के अलावा अन्य दुकान पर {count} संग्रह।",
        "mr": "नेमलेल्या दुकानाव्यतिरिक्त इतर दुकानात {count} संकलने.",
    },
    "RISK_CANCELLATIONS": {
        "en": "{count} bookings cancelled in the window.",
        "hi": "इस अवधि में {count} बुकिंग रद्द की गईं।",
        "mr": "या कालावधीत {count} बुकिंग रद्द.",
    },
    # Shop monitoring
    "SHOP_LEDGER_MISMATCH": {
        "en": "{item}: recorded stock {actual} differs from the ledger balance {expected} (variance {variance}).",
        "hi": "{item}: दर्ज स्टॉक {actual} लेजर शेष {expected} से भिन्न है (अंतर {variance})।",
        "mr": "{item}: नोंदलेला साठा {actual} लेजर शिल्लक {expected} पेक्षा वेगळा (फरक {variance}).",
    },
    "SHOP_LEDGER_GAP": {
        "en": "{item}: {count} stock change(s) made outside the ledger.",
        "hi": "{item}: लेजर के बाहर {count} स्टॉक परिवर्तन।",
        "mr": "{item}: लेजरबाहेर {count} साठा बदल.",
    },
    "SHOP_HIGH_FAILED_VERIFICATION": {
        "en": "{failed} of {total} verifications failed or were blocked ({rate}%).",
        "hi": "{total} में से {failed} सत्यापन विफल या अवरुद्ध ({rate}%)।",
        "mr": "{total} पैकी {failed} पडताळण्या अयशस्वी किंवा अवरोधित ({rate}%).",
    },
    "SHOP_HIGH_NO_SHOW": {
        "en": "{count} booked tokens were never collected ({rate}% no-show).",
        "hi": "{count} बुक टोकन कभी एकत्र नहीं किए गए ({rate}% अनुपस्थित)।",
        "mr": "{count} बुक टोकन कधीच घेतले नाहीत ({rate}% गैरहजर).",
    },
    "SHOP_UNDER_ISSUE": {
        "en": "{item}: issued {issued} of {booked} booked ({rate}%).",
        "hi": "{item}: {booked} बुक में से {issued} जारी ({rate}%)।",
        "mr": "{item}: {booked} बुकपैकी {issued} दिले ({rate}%).",
    },
    "SHOP_HIGH_DAMAGE": {
        "en": "{item}: {damaged} written off as damaged ({rate}% of the stock handled in the period).",
        "hi": "{item}: {damaged} क्षतिग्रस्त लिखा गया (अवधि में संभाले गए स्टॉक का {rate}%)।",
        "mr": "{item}: {damaged} खराब म्हणून नोंदले (कालावधीत हाताळलेल्या साठ्याच्या {rate}%).",
    },
    # Queue
    "QUEUE_MEASURED": {
        "en": "Average service time measured from {samples} recent collections.",
        "hi": "औसत सेवा समय {samples} हालिया संग्रहों से मापा गया।",
        "mr": "सरासरी सेवा वेळ {samples} अलीकडील संकलनांवरून मोजली.",
    },
    "QUEUE_DEFAULT": {
        "en": "Not enough recent collections to measure service time; using the configured {minutes} min estimate.",
        "hi": "सेवा समय मापने के लिए पर्याप्त हालिया संग्रह नहीं; निर्धारित {minutes} मिनट अनुमान उपयोग किया गया।",
        "mr": "सेवा वेळ मोजण्यासाठी पुरेशी अलीकडील संकलने नाहीत; ठरवलेला {minutes} मिनिटांचा अंदाज वापरला.",
    },
    # Forecast data quality
    "FORECAST_ANOMALOUS": {
        "en": "{count} unusually high day(s) in the history were capped before forecasting.",
        "hi": "पूर्वानुमान से पहले इतिहास के {count} असामान्य रूप से ऊँचे दिन सीमित किए गए।",
        "mr": "अंदाजापूर्वी इतिहासातील {count} असामान्यपणे जास्त दिवस मर्यादित केले.",
    },
    "LIMIT_SHORT_HISTORY": {
        "en": "Less than 60 days of history: treat as indicative only.",
        "hi": "60 दिनों से कम इतिहास: केवल संकेतात्मक मानें।",
        "mr": "60 दिवसांपेक्षा कमी इतिहास: केवळ सूचक समजा.",
    },
    "LIMIT_NO_SEASONALITY": {
        "en": "Festival or seasonal peaks are not modelled explicitly.",
        "hi": "त्योहार या मौसमी चरम स्पष्ट रूप से मॉडल नहीं किए गए हैं।",
        "mr": "सण किंवा हंगामी वाढ स्पष्टपणे मॉडेल केलेली नाही.",
    },
    # Alerts
    "ALERT_FORECAST_RISK": {
        "en": "Forecast demand of {need} over the next {days} days exceeds the {have} available after bookings ({confidence} confidence).",
        "hi": "अगले {days} दिनों की अनुमानित मांग {need} है, जो बुकिंग के बाद उपलब्ध {have} से अधिक है ({confidence} विश्वसनीयता)।",
        "mr": "पुढील {days} दिवसांची अंदाजित मागणी {need}, बुकिंगनंतर उपलब्ध {have} पेक्षा जास्त ({confidence} विश्वासार्हता).",
    },
    "ALERT_DEMAND_SPIKE": {
        "en": "{recent} issued in the last 7 days — {ratio}x the usual {weekly} per week.",
        "hi": "पिछले 7 दिनों में {recent} जारी — सामान्य {weekly} प्रति सप्ताह का {ratio} गुना।",
        "mr": "गेल्या 7 दिवसांत {recent} दिले — नेहमीच्या {weekly} प्रति आठवड्याच्या {ratio} पट.",
    },
    "ACTION_REORDER": {"en": "Raise a stock indent / reorder for this item.", "hi": "इस सामग्री के लिए स्टॉक मांग/पुनः ऑर्डर करें।", "mr": "या वस्तूसाठी साठा मागणी / पुनर्मागणी करा."},
    "ACTION_AUDIT_STOCK": {"en": "Physically verify stock and reconcile the ledger.", "hi": "स्टॉक का भौतिक सत्यापन करें और लेजर मिलान करें।", "mr": "साठ्याची प्रत्यक्ष पडताळणी करून लेजर जुळवा."},
    "ACTION_CHECK_DEMAND": {"en": "Check whether the rise is genuine (new families, festival) before reordering.", "hi": "पुनः ऑर्डर से पहले जांचें कि वृद्धि वास्तविक है (नए परिवार, त्योहार)।", "mr": "पुनर्मागणीपूर्वी वाढ खरी आहे का (नवीन कुटुंबे, सण) ते तपासा."},
    "ACTION_REVIEW_DAMAGE": {"en": "Review damage write-offs and storage conditions.", "hi": "क्षति प्रविष्टियों और भंडारण स्थिति की समीक्षा करें।", "mr": "खराब साठ्याच्या नोंदी आणि साठवण स्थितीचे पुनरावलोकन करा."},
    "ACTION_REVIEW_ISSUE": {"en": "Review why booked quantities were not fully issued.", "hi": "समीक्षा करें कि बुक मात्रा पूरी क्यों जारी नहीं हुई।", "mr": "बुक केलेले प्रमाण पूर्ण का दिले नाही ते तपासा."},
    # Disclaimer
    "RISK_DISCLAIMER": {
        "en": "Decision support only. A risk score is not proof of fraud and must never be used to deny rations automatically.",
        "hi": "केवल निर्णय सहायता। जोखिम स्कोर धोखाधड़ी का प्रमाण नहीं है और इसके आधार पर स्वतः राशन नहीं रोका जाना चाहिए।",
        "mr": "फक्त निर्णय सहाय्य. जोखीम गुण फसवणुकीचा पुरावा नाही; त्यावरून आपोआप रेशन नाकारू नये.",
    },
}

SUPPORTED = ("en", "hi", "mr")


def normalize_lang(lang: str | None) -> str:
    return lang if lang in SUPPORTED else "en"


def reason(code: str, lang: str, **params) -> dict:
    template = MESSAGES.get(code, {}).get(lang) or MESSAGES.get(code, {}).get("en", code)
    return {"code": code, "params": params, "text": template.format(**params)}
