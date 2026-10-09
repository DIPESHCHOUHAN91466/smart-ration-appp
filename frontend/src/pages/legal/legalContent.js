// Policy pages required for Indian government websites (GIGW): Privacy Policy, Terms of Use, Accessibility Statement.
// One structure per language (en, hi, mr), so reviewers see every language side by side and none can drift.
//
// Published 2026-10-09 for the public demo operated by Dipesh Chouhan. Review with a lawyer before government or
// real-beneficiary use; the Hindi and Marathi texts need an official translation check.

export const LEGAL_REVIEWED = "9 October 2026";

export const legalContent = {
  en: {
    privacy: {
      title: "Privacy Policy",
      sections: [
        ["Who we are", ["This service is operated by Dipesh Chouhan (the \"Data Fiduciary\" under the Digital Personal Data Protection Act, 2023). It helps ration card holders book a time to collect their ration, lets fair-price shops record collections, and lets government officials oversee distribution."]],
        ["What we collect and why", [
          "Account: name, mobile number, email address and role, to sign you in.",
          "Ration records: ration card, family members, scheme and entitlement, bookings, tokens and collections, to provide your ration.",
          "Complaints: what you report, to resolve it and tell you the outcome.",
          "Aadhaar: the service only records whether Aadhaar is verified. Your Aadhaar number is never shown in full, and you are never asked to type it.",
          "We collect only what is needed for these purposes and do not use it for anything else.",
        ]],
        ["Consent", ["By registering you consent to this processing for the purposes above. You can withdraw consent at any time by asking us to close your account (see \"Your rights\"); this does not affect processing already done or records the law requires us to keep."]],
        ["Sharing", ["Your information is shared only to provide the ration service: with your ration shop (to serve you) and with government officials who oversee the public distribution system, and with others only where the law requires it. We do not sell your information. The service contains no advertising and no tracking tools."]],
        ["Where and how long it is kept", ["Data is stored on servers located in India (Microsoft Azure, India South Central region). Records are kept for as long as your account is active and up to one year after it is closed, to provide the service and to handle complaints or disputes and then deleted or anonymised."]],
        ["Security", ["Connections are encrypted (HTTPS, and TLS to the database). Passwords are stored only as secure hashes. Sign-in sessions expire. Important actions are recorded in an audit log that does not contain your messages or personal identifiers beyond what is needed."]],
        ["Your rights", ["Under the DPDP Act you can ask to see a summary of your data, correct it, have it erased, and have a grievance addressed, and you may nominate a person to exercise these rights for you. Write to our Grievance Officer: Dipesh Chouhan, dipeshchouhan9146@gmail.com. To delete your account, use \"Close my account\" under My account in the app or Settings on the website, or write to that address. We will reply within 30 days. If you are not satisfied you may approach the Data Protection Board of India."]],
        ["Children", ["Accounts are for adults. Children's details appear only as family members on a ration card, are shown only to the card holder and the people who serve them, and are never used for any other purpose."]],
        ["Changes", ["If this policy changes, the new version is published here with a new date."]],
      ],
    },
    terms: {
      title: "Terms of Use",
      sections: [
        ["Using this service", ["This website and app are provided by Dipesh Chouhan to help citizens collect their ration and to support fair-price shops and officials. By using it you agree to these terms."]],
        ["Your account", ["Keep your password and one-time codes private; we will never ask for them. You are responsible for activity under your account. Tell us at once at dipeshchouhan9146@gmail.com if you think someone else has used it."]],
        ["Fair use", ["Do not try to access other people's records, interfere with the service, upload harmful content, or use automated tools against it. Misuse may be reported to the authorities under the Information Technology Act, 2000."]],
        ["Accuracy", ["We work to keep information correct, but entitlements and records are decided by the responsible government department. If something looks wrong, contact your ration office or file a complaint in the service."]],
        ["Copyright and hyperlinking", ["Content on this site may be reproduced free of charge with acknowledgement of the source, but not in a misleading way or for commercial purposes. Links to this site are welcome; pages of this site may not be loaded inside frames on other sites. Links to other websites are provided for convenience; we are not responsible for their content."]],
        ["Law", ["These terms are governed by the laws of India. Disputes are subject to the jurisdiction of the competent courts in India."]],
      ],
    },
    accessibility: {
      title: "Accessibility Statement",
      sections: [
        ["Our commitment", ["We want everyone to be able to use this service, including people with disabilities, older people and first-time internet users. We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.1 at level AA and the Guidelines for Indian Government Websites (GIGW)."]],
        ["What you can do", [
          "Use the whole website with a keyboard; a \"Skip to main content\" link is the first thing on every page.",
          "Use a screen reader: controls are labelled, and messages and errors are announced.",
          "Read every page in English, Hindi or Marathi.",
          "After signing in, choose larger text, high contrast and reduced motion in Settings.",
          "Ask the help assistant by voice and have answers read aloud.",
        ]],
        ["Known limitations", ["The shop map is a visual map; the same information is available as a list on the Shops page."]],
        ["Feedback", ["If you find something hard to use, tell us at dipeshchouhan9146@gmail.com. Please describe the page and the problem; we aim to reply within 7 working days."]],
      ],
    },
  },

  hi: {
    privacy: {
      title: "गोपनीयता नीति",
      sections: [
        ["हम कौन हैं", ["यह सेवा दीपेश चौहान द्वारा संचालित है (डिजिटल व्यक्तिगत डेटा संरक्षण अधिनियम, 2023 के तहत \"डेटा फ़िड्यूशियरी\")। यह राशन कार्ड धारकों को राशन लेने का समय बुक करने में, उचित मूल्य की दुकानों को वितरण दर्ज करने में और सरकारी अधिकारियों को वितरण की निगरानी में मदद करती है।"]],
        ["हम क्या लेते हैं और क्यों", [
          "खाता: नाम, मोबाइल नंबर, ईमेल और भूमिका, आपको साइन इन कराने के लिए।",
          "राशन रिकॉर्ड: राशन कार्ड, परिवार के सदस्य, योजना और हक, बुकिंग, टोकन और वितरण, आपको राशन देने के लिए।",
          "शिकायतें: आपने जो बताया, उसे सुलझाने और परिणाम बताने के लिए।",
          "आधार: सेवा केवल यह दर्ज करती है कि आधार सत्यापित है या नहीं। आपका आधार नंबर कभी पूरा नहीं दिखाया जाता और आपसे उसे लिखने को नहीं कहा जाता।",
          "हम इन उद्देश्यों के लिए केवल ज़रूरी जानकारी लेते हैं और उसका कोई और उपयोग नहीं करते।",
        ]],
        ["सहमति", ["पंजीकरण करके आप ऊपर दिए उद्देश्यों के लिए इस प्रसंस्करण की सहमति देते हैं। आप कभी भी अपना खाता बंद करने को कहकर सहमति वापस ले सकते हैं (\"आपके अधिकार\" देखें); इससे पहले हो चुका प्रसंस्करण या कानून द्वारा ज़रूरी रिकॉर्ड प्रभावित नहीं होते।"]],
        ["साझा करना", ["आपकी जानकारी केवल राशन सेवा देने के लिए साझा की जाती है: आपकी राशन दुकान के साथ (आपको सेवा देने के लिए), सार्वजनिक वितरण प्रणाली की निगरानी करने वाले सरकारी अधिकारियों के साथ, और अन्य के साथ केवल तब जब कानून ऐसा माँगे। हम आपकी जानकारी नहीं बेचते। सेवा में कोई विज्ञापन या ट्रैकिंग टूल नहीं है।"]],
        ["कहाँ और कितने समय तक रखा जाता है", ["डेटा भारत (Microsoft Azure, India South Central क्षेत्र) में स्थित सर्वरों पर रखा जाता है। रिकॉर्ड जब तक आपका खाता सक्रिय है और बंद होने के बाद एक वर्ष तक, सेवा देने और शिकायतों या विवादों के निपटारे के लिए तक रखे जाते हैं और फिर हटा दिए जाते हैं या अनाम कर दिए जाते हैं।"]],
        ["सुरक्षा", ["कनेक्शन एन्क्रिप्टेड हैं (HTTPS, और डेटाबेस तक TLS)। पासवर्ड केवल सुरक्षित हैश के रूप में रखे जाते हैं। साइन-इन सत्र समाप्त हो जाते हैं। महत्वपूर्ण कार्य एक ऑडिट लॉग में दर्ज होते हैं जिसमें आपके संदेश या अनावश्यक व्यक्तिगत पहचान नहीं होती।"]],
        ["आपके अधिकार", ["DPDP अधिनियम के तहत आप अपने डेटा का सारांश देखने, उसे सुधारने, हटवाने और अपनी शिकायत का निवारण माँग सकते हैं, और इन अधिकारों के लिए किसी व्यक्ति को नामित कर सकते हैं। हमारे शिकायत अधिकारी को लिखें: दीपेश चौहान, dipeshchouhan9146@gmail.com। अपना खाता हटाने के लिए ऐप में \"मेरा खाता\" या वेबसाइट पर सेटिंग्स में \"मेरा खाता बंद करें\" चुनें, या इसी पते पर लिखें। हम 30 दिनों में उत्तर देंगे। संतुष्ट न होने पर आप भारतीय डेटा संरक्षण बोर्ड से संपर्क कर सकते हैं।"]],
        ["बच्चे", ["खाते वयस्कों के लिए हैं। बच्चों का विवरण केवल राशन कार्ड पर परिवार के सदस्य के रूप में आता है, केवल कार्ड धारक और उन्हें सेवा देने वालों को दिखता है, और किसी और उद्देश्य के लिए उपयोग नहीं होता।"]],
        ["बदलाव", ["यह नीति बदलने पर नया संस्करण नई तारीख के साथ यहीं प्रकाशित किया जाएगा।"]],
      ],
    },
    terms: {
      title: "उपयोग की शर्तें",
      sections: [
        ["इस सेवा का उपयोग", ["यह वेबसाइट और ऐप दीपेश चौहान द्वारा नागरिकों को राशन लेने में और उचित मूल्य की दुकानों व अधिकारियों की सहायता के लिए दिए गए हैं। इसका उपयोग करके आप इन शर्तों से सहमत होते हैं।"]],
        ["आपका खाता", ["अपना पासवर्ड और एक-बार के कोड गोपनीय रखें; हम उन्हें कभी नहीं माँगेंगे। आपके खाते से होने वाली गतिविधि की ज़िम्मेदारी आपकी है। यदि आपको लगे कि किसी और ने इसका उपयोग किया है, तो तुरंत dipeshchouhan9146@gmail.com पर बताएं।"]],
        ["उचित उपयोग", ["दूसरों के रिकॉर्ड देखने की कोशिश न करें, सेवा में बाधा न डालें, हानिकारक सामग्री अपलोड न करें और इसके विरुद्ध स्वचालित टूल का उपयोग न करें। दुरुपयोग की सूचना सूचना प्रौद्योगिकी अधिनियम, 2000 के तहत अधिकारियों को दी जा सकती है।"]],
        ["सटीकता", ["हम जानकारी सही रखने का प्रयास करते हैं, पर हक और रिकॉर्ड संबंधित सरकारी विभाग तय करता है। कुछ गलत लगे तो अपने राशन कार्यालय से संपर्क करें या सेवा में शिकायत दर्ज करें।"]],
        ["कॉपीराइट और हाइपरलिंक", ["इस साइट की सामग्री स्रोत का उल्लेख करके निःशुल्क पुनः प्रस्तुत की जा सकती है, पर भ्रामक ढंग से या व्यावसायिक उद्देश्य से नहीं। इस साइट के लिंक का स्वागत है; इसके पेज दूसरी साइटों के फ़्रेम में नहीं दिखाए जा सकते। अन्य वेबसाइटों के लिंक सुविधा के लिए हैं; उनकी सामग्री के लिए हम ज़िम्मेदार नहीं हैं।"]],
        ["कानून", ["ये शर्तें भारत के कानूनों के अधीन हैं। विवाद भारत के सक्षम न्यायालयों के क्षेत्राधिकार में होंगे।"]],
      ],
    },
    accessibility: {
      title: "सुगम्यता वक्तव्य",
      sections: [
        ["हमारी प्रतिबद्धता", ["हम चाहते हैं कि दिव्यांगजन, बुज़ुर्ग और पहली बार इंटरनेट उपयोग करने वाले सहित सभी लोग यह सेवा उपयोग कर सकें। हमारा लक्ष्य वेब सामग्री सुगम्यता दिशानिर्देश (WCAG) 2.1 स्तर AA और भारत सरकार की वेबसाइटों के दिशानिर्देश (GIGW) पूरे करना है।"]],
        ["आप क्या कर सकते हैं", [
          "पूरी वेबसाइट कीबोर्ड से चलाएं; हर पेज पर सबसे पहले \"मुख्य सामग्री पर जाएं\" लिंक है।",
          "स्क्रीन रीडर का उपयोग करें: नियंत्रणों पर लेबल हैं, और संदेश व त्रुटियाँ पढ़कर सुनाई जाती हैं।",
          "हर पेज अंग्रेज़ी, हिंदी या मराठी में पढ़ें।",
          "साइन इन के बाद सेटिंग्स में बड़ा टेक्स्ट, उच्च कंट्रास्ट और कम एनिमेशन चुनें।",
          "सहायक से बोलकर पूछें और उत्तर सुनें।",
        ]],
        ["ज्ञात सीमाएँ", ["दुकानों का नक्शा दृश्य है; वही जानकारी दुकानें पेज पर सूची के रूप में उपलब्ध है।"]],
        ["सुझाव", ["कुछ उपयोग करने में कठिन लगे तो हमें dipeshchouhan9146@gmail.com पर बताएं। पेज और समस्या बताएं; हम 7 कार्य दिवसों में उत्तर देने का प्रयास करते हैं।"]],
      ],
    },
  },

  mr: {
    privacy: {
      title: "गोपनीयता धोरण",
      sections: [
        ["आम्ही कोण आहोत", ["ही सेवा दीपेश चौहान चालवते (डिजिटल वैयक्तिक डेटा संरक्षण अधिनियम, 2023 अंतर्गत \"डेटा फिड्युशियरी\"). ती शिधापत्रिकाधारकांना रेशन घेण्याची वेळ बुक करण्यास, रास्त भाव दुकानांना वितरण नोंदवण्यास आणि सरकारी अधिकाऱ्यांना वितरणावर देखरेख ठेवण्यास मदत करते."]],
        ["आम्ही काय घेतो आणि का", [
          "खाते: नाव, मोबाइल क्रमांक, ईमेल आणि भूमिका, तुम्हाला साइन इन करण्यासाठी.",
          "रेशन नोंदी: शिधापत्रिका, कुटुंबातील सदस्य, योजना आणि हक्क, बुकिंग, टोकन आणि वितरण, तुम्हाला रेशन देण्यासाठी.",
          "तक्रारी: तुम्ही कळवलेले, ते सोडवण्यासाठी आणि निकाल कळवण्यासाठी.",
          "आधार: सेवा फक्त आधार पडताळला आहे की नाही हे नोंदवते. तुमचा आधार क्रमांक कधीही पूर्ण दाखवला जात नाही आणि तो लिहायला सांगितले जात नाही.",
          "आम्ही या उद्देशांसाठी फक्त आवश्यक माहिती घेतो आणि तिचा इतर कोणताही वापर करत नाही.",
        ]],
        ["संमती", ["नोंदणी करून तुम्ही वरील उद्देशांसाठी या प्रक्रियेस संमती देता. तुमचे खाते बंद करण्यास सांगून तुम्ही कधीही संमती मागे घेऊ शकता (\"तुमचे अधिकार\" पाहा); यामुळे आधी झालेली प्रक्रिया किंवा कायद्याने आवश्यक नोंदी प्रभावित होत नाहीत."]],
        ["सामायिकरण", ["तुमची माहिती फक्त रेशन सेवा देण्यासाठी सामायिक केली जाते: तुमच्या रेशन दुकानासोबत (तुम्हाला सेवा देण्यासाठी), सार्वजनिक वितरण प्रणालीवर देखरेख ठेवणाऱ्या सरकारी अधिकाऱ्यांसोबत, आणि इतरांसोबत फक्त कायद्याने आवश्यक असेल तेव्हा. आम्ही तुमची माहिती विकत नाही. सेवेत कोणतीही जाहिरात किंवा ट्रॅकिंग साधने नाहीत."]],
        ["कुठे आणि किती काळ ठेवली जाते", ["डेटा भारत (Microsoft Azure, India South Central प्रदेश) येथील सर्व्हरवर ठेवला जातो. नोंदी तुमचे खाते सक्रिय असेपर्यंत आणि बंद झाल्यानंतर एक वर्षापर्यंत, सेवा देण्यासाठी आणि तक्रारी किंवा वाद सोडवण्यासाठी ठेवल्या जातात आणि नंतर हटवल्या किंवा अनामिक केल्या जातात."]],
        ["सुरक्षा", ["जोडण्या एन्क्रिप्टेड आहेत (HTTPS, आणि डेटाबेसपर्यंत TLS). पासवर्ड फक्त सुरक्षित हॅश स्वरूपात ठेवले जातात. साइन-इन सत्रे कालबाह्य होतात. महत्त्वाच्या कृती ऑडिट लॉगमध्ये नोंदवल्या जातात ज्यात तुमचे संदेश किंवा अनावश्यक वैयक्तिक ओळख नसते."]],
        ["तुमचे अधिकार", ["DPDP अधिनियमानुसार तुम्ही तुमच्या डेटाचा सारांश पाहणे, तो दुरुस्त करणे, हटवणे आणि तक्रार निवारण मागू शकता, आणि या अधिकारांसाठी एखाद्या व्यक्तीला नामनिर्देशित करू शकता. आमच्या तक्रार अधिकाऱ्याला लिहा: दीपेश चौहान, dipeshchouhan9146@gmail.com. खाते हटवण्यासाठी ॲपमध्ये \"माझे खाते\" किंवा वेबसाइटवर सेटिंग्जमध्ये \"माझे खाते बंद करा\" निवडा, किंवा याच पत्त्यावर लिहा. आम्ही 30 दिवसांत उत्तर देऊ. समाधान न झाल्यास तुम्ही भारतीय डेटा संरक्षण मंडळाकडे जाऊ शकता."]],
        ["मुले", ["खाती प्रौढांसाठी आहेत. मुलांचा तपशील फक्त शिधापत्रिकेवरील कुटुंब सदस्य म्हणून येतो, फक्त पत्रिकाधारक आणि त्यांना सेवा देणाऱ्यांना दिसतो, आणि इतर कोणत्याही उद्देशासाठी वापरला जात नाही."]],
        ["बदल", ["हे धोरण बदलल्यास नवीन आवृत्ती नवीन तारखेसह येथेच प्रकाशित केली जाईल."]],
      ],
    },
    terms: {
      title: "वापराच्या अटी",
      sections: [
        ["ही सेवा वापरणे", ["ही वेबसाइट आणि ॲप दीपेश चौहान नागरिकांना रेशन घेण्यास आणि रास्त भाव दुकाने व अधिकाऱ्यांना मदत करण्यासाठी देते. ती वापरून तुम्ही या अटी मान्य करता."]],
        ["तुमचे खाते", ["तुमचा पासवर्ड आणि एकदाच वापरायचे कोड गोपनीय ठेवा; आम्ही ते कधीही मागणार नाही. तुमच्या खात्यावरील कृतींची जबाबदारी तुमची आहे. दुसऱ्या कोणी ते वापरले असे वाटल्यास लगेच dipeshchouhan9146@gmail.com वर कळवा."]],
        ["योग्य वापर", ["इतरांच्या नोंदी पाहण्याचा प्रयत्न करू नका, सेवेत अडथळा आणू नका, हानिकारक मजकूर अपलोड करू नका आणि तिच्याविरुद्ध स्वयंचलित साधने वापरू नका. गैरवापराची माहिती माहिती तंत्रज्ञान अधिनियम, 2000 अंतर्गत अधिकाऱ्यांना दिली जाऊ शकते."]],
        ["अचूकता", ["आम्ही माहिती अचूक ठेवण्याचा प्रयत्न करतो, पण हक्क आणि नोंदी संबंधित सरकारी विभाग ठरवतो. काही चुकीचे वाटल्यास तुमच्या रेशन कार्यालयाशी संपर्क साधा किंवा सेवेत तक्रार नोंदवा."]],
        ["कॉपीराइट आणि हायपरलिंक", ["या साइटवरील मजकूर स्रोताचा उल्लेख करून विनामूल्य पुनर्प्रकाशित करता येतो, पण दिशाभूल करणाऱ्या पद्धतीने किंवा व्यावसायिक हेतूने नाही. या साइटचे दुवे स्वागतार्ह आहेत; तिची पाने इतर साइटच्या फ्रेममध्ये दाखवता येणार नाहीत. इतर वेबसाइटचे दुवे सोयीसाठी आहेत; त्यांच्या मजकुरासाठी आम्ही जबाबदार नाही."]],
        ["कायदा", ["या अटी भारताच्या कायद्यांच्या अधीन आहेत. वाद भारतातील सक्षम न्यायालयांच्या अधिकारक्षेत्रात असतील."]],
      ],
    },
    accessibility: {
      title: "सुलभता निवेदन",
      sections: [
        ["आमची बांधिलकी", ["दिव्यांग व्यक्ती, ज्येष्ठ नागरिक आणि पहिल्यांदाच इंटरनेट वापरणारे यांच्यासह सर्वांना ही सेवा वापरता यावी अशी आमची इच्छा आहे. वेब मजकूर सुलभता मार्गदर्शक तत्त्वे (WCAG) 2.1 स्तर AA आणि भारत सरकारच्या वेबसाइटसाठीची मार्गदर्शक तत्त्वे (GIGW) पूर्ण करणे हे आमचे उद्दिष्ट आहे."]],
        ["तुम्ही काय करू शकता", [
          "संपूर्ण वेबसाइट कीबोर्डने वापरा; प्रत्येक पानावर सर्वप्रथम \"मुख्य मजकुराकडे जा\" दुवा आहे.",
          "स्क्रीन रीडर वापरा: नियंत्रणांना लेबल आहेत, आणि संदेश व त्रुटी वाचून दाखवल्या जातात.",
          "प्रत्येक पान इंग्रजी, हिंदी किंवा मराठीत वाचा.",
          "साइन इन केल्यानंतर सेटिंग्जमध्ये मोठा मजकूर, उच्च कॉन्ट्रास्ट आणि कमी ॲनिमेशन निवडा.",
          "सहाय्यकाला बोलून विचारा आणि उत्तरे ऐका.",
        ]],
        ["ज्ञात मर्यादा", ["दुकानांचा नकाशा दृश्य आहे; तीच माहिती दुकाने पानावर यादी स्वरूपात उपलब्ध आहे."]],
        ["अभिप्राय", ["काही वापरण्यास कठीण वाटल्यास आम्हाला dipeshchouhan9146@gmail.com वर कळवा. पान आणि समस्या सांगा; आम्ही 7 कामकाजाच्या दिवसांत उत्तर देण्याचा प्रयत्न करतो."]],
      ],
    },
  },
};
