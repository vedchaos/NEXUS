#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Internationalization Server"""

import json
import sys
import re
import unicodedata
from collections import Counter

TOOLS = [
    {"name": "ctz_i18n_detect", "description": "Detect language of text via Unicode ranges + common words", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "ctz_i18n_translate", "description": "Translate text between languages", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "source": {"type": "string", "default": "auto"}, "target": {"type": "string"}}, "required": ["text", "target"]}},
    {"name": "ctz_i18n_localize", "description": "Localize text for a locale (numbers, dates, etc.)", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}, "locale": {"type": "string"}}, "required": ["text", "locale"]}},
    {"name": "ctz_i18n_pluralize", "description": "Pluralize a word for different languages", "inputSchema": {"type": "object", "properties": {"word": {"type": "string"}, "count": {"type": "integer"}, "language": {"type": "string"}}, "required": ["word", "count", "language"]}},
    {"name": "ctz_i18n_formats", "description": "Get locale-specific formats (date, number, currency)", "inputSchema": {"type": "object", "properties": {"locale": {"type": "string"}}, "required": ["locale"]}},
    {"name": "ctz_i18n_languages", "description": "List supported languages", "inputSchema": {"type": "object", "properties": {}}},
]

LANGUAGES = {
    "en": {"name": "English", "native": "English", "dir": "ltr", "family": "germanic"},
    "es": {"name": "Spanish", "native": "Espanol", "dir": "ltr", "family": "romance"},
    "fr": {"name": "French", "native": "Francais", "dir": "ltr", "family": "romance"},
    "de": {"name": "German", "native": "Deutsch", "dir": "ltr", "family": "germanic"},
    "it": {"name": "Italian", "native": "Italiano", "dir": "ltr", "family": "romance"},
    "pt": {"name": "Portuguese", "native": "Portugues", "dir": "ltr", "family": "romance"},
    "ru": {"name": "Russian", "native": "Pусский", "dir": "ltr", "family": "slavic"},
    "zh": {"name": "Chinese", "native": "中文", "dir": "ltr", "family": "sinitic"},
    "ja": {"name": "Japanese", "native": "日本語", "dir": "ltr", "family": "japonic"},
    "ko": {"name": "Korean", "native": "한국어", "dir": "ltr", "family": "koreanic"},
    "ar": {"name": "Arabic", "native": "العربية", "dir": "rtl", "family": "semitic"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "dir": "ltr", "family": "indo-aryan"},
    "tr": {"name": "Turkish", "native": "Turkce", "dir": "ltr", "family": "turkic"},
    "nl": {"name": "Dutch", "native": "Nederlands", "dir": "ltr", "family": "germanic"},
    "pl": {"name": "Polish", "native": "Polski", "dir": "ltr", "family": "slavic"},
    "sv": {"name": "Swedish", "native": "Svenska", "dir": "ltr", "family": "germanic"},
    "th": {"name": "Thai", "native": "ไทย", "dir": "ltr", "family": "kra-dai"},
    "vi": {"name": "Vietnamese", "native": "Tieng Viet", "dir": "ltr", "family": "austroasiatic"},
    "uk": {"name": "Ukrainian", "native": "Українська", "dir": "ltr", "family": "slavic"},
    "el": {"name": "Greek", "native": "Ελληνικά", "dir": "ltr", "family": "hellenic"},
    "cs": {"name": "Czech", "native": "Cestina", "dir": "ltr", "family": "slavic"},
    "ro": {"name": "Romanian", "native": "Romana", "dir": "ltr", "family": "romance"},
    "he": {"name": "Hebrew", "native": "עברית", "dir": "rtl", "family": "semitic"},
    "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "dir": "ltr", "family": "austronesian"},
    "ms": {"name": "Malay", "native": "Bahasa Melayu", "dir": "ltr", "family": "austronesian"},
    "fi": {"name": "Finnish", "native": "Suomi", "dir": "ltr", "family": "uralic"},
    "da": {"name": "Danish", "native": "Dansk", "dir": "ltr", "family": "germanic"},
    "no": {"name": "Norwegian", "native": "Norsk", "dir": "ltr", "family": "germanic"},
}

COMMON_WORDS = {
    "en": set("the is are was were be been being have has had do does did will would shall should may might can could of in to for with on at from by as into through during before after above below between out off over under".split()),
    "es": set("el la los las un una unos unas es son fue ser estar tener hacer ir hay puede del al cuando como pero mas ya tambien este esta esto muy por que sin sobre".split()),
    "fr": set("le la les un une des est sont etre avoir faire aller il elle on nous vous ils elles mais plus tres aussi peut que qui dans par pour".split()),
    "de": set("der die das ein eine einer eines einem den dem und ist sind ich du er sie wir ihr sie haben kann wird nicht als auch nach oder wenn aber".split()),
    "it": set("il lo la le un una uno di da in con su per che non si e sono ha come piu anche questo questa del della".split()),
    "pt": set("o a os as um uma uns uma e e estar ter fazer como mais muito por para com nao tambem pode ja este esta isto".split()),
    "ru": set("и в не на я что это он как а то все она так его но да ты к у же вы будет из за мне ".split()),
    "zh": set("的是了不在有我他这中大来上个国和也子时道说们那要没出会能对么下自之年过然后事里人".split()),
    "ja": set("の は が を に で と も し て い な だ から まで より など ため こと もの ある いる する なる ない".split()),
    "ko": set("은 는 이 가 을 를 에 에서 에게 의 로 과 와 과 도 나 는데 며 하지만 그리고 또는 또는 때문에 하지만 하지만".split()),
    "ar": set("في على من هو هي إلى أن لا لكن قد هذا هذه ثم عند بعد قبل كل أي أكثر".split()),
    "hi": set("में के है और एक तो भी यह वह कि से को पर ने था थे हैं गया था करने के लिए". split()),
    "tr": "bir ve bu da de ile icin ile ile ama ile olan gibi daha da da da".split(),
    "nl": "de het een van en in is op dat niet met voor maar kan er nog wat zo".split(),
    "pl": "nie jest do sie jak ale co tu tak sie ze tam juz po jest".split(),
    "sv": "och det att en i den kan som har var men inte ett till om".split(),
    "th": "และ เป็น ใน ที่ มี ได้ ไม่ นี้ จะ ของ ให้ ไป ทำ คือ มามา ก็".split(),
    "vi": "va la cung co nhung doi khi nao do khong the tinh".split(),
    "uk": "і в на не що це як але також до за від по який те той цей".split(),
    "el": "και ειναι το να σε αυτο που αλλα με για οι τα οτι".split(),
    "cs": "a v je se na to z jsou tak do ale co nebo jako".split(),
    "ro": "si in este la pe un o cu nu mai sunt ca dar din".split(),
    "he": "של את זה על לא כן יש גם אם אני הוא היא но было".split(),
    "id": "dan di yang dari adalah untuk dengan ini itu tidak pada".split(),
    "ms": "dan di yang dari adalah untuk dengan ini itu tidak pada".split(),
    "fi": "ja ei ole on se tai mutta kuin vaikka tama miten nyt jo".split(),
    "da": "og i er det den til at ikke med har vi som kan".split(),
    "no": "og i er det den til at ikke med har vi som kan vil".split(),
}

TRANSLATION_DICT = {
    ("en", "es"): {"hello": "hola", "goodbye": "adios", "thank you": "gracias", "please": "por favor", "yes": "si", "no": "no", "good morning": "buenos dias", "good night": "buenas noches", "how are you": "como estas", "welcome": "bienvenido"},
    ("en", "fr"): {"hello": "bonjour", "goodbye": "au revoir", "thank you": "merci", "please": "s'il vous plait", "yes": "oui", "no": "non", "good morning": "bonjour", "good night": "bonne nuit", "how are you": "comment allez-vous", "welcome": "bienvenue"},
    ("en", "de"): {"hello": "hallo", "goodbye": "auf wiedersehen", "thank you": "danke", "please": "bitte", "yes": "ja", "no": "nein", "good morning": "guten morgen", "good night": "gute nacht", "how are you": "wie geht es ihnen", "welcome": "willkommen"},
    ("en", "ja"): {"hello": "こんにちは", "goodbye": "さようなら", "thank you": "ありがとう", "please": "お願いします", "yes": "はい", "no": "いいえ", "good morning": "おはようございます", "good night": "おやすみなさい", "how are you": "お元気ですか", "welcome": "ようこそ"},
    ("en", "zh"): {"hello": "你好", "goodbye": "再见", "thank you": "谢谢", "please": "请", "yes": "是", "no": "不", "good morning": "早上好", "good night": "晚安", "how are you": "你好吗", "welcome": "欢迎"},
    ("en", "ko"): {"hello": "안녕하세요", "goodbye": "안녕히 가세요", "thank you": "감사합니다", "please": "부탁합니다", "yes": "네", "no": "아니요", "good morning": "좋은 아침", "good night": "잘 자요", "how are you": "어떻게 지내세요", "welcome": "환영합니다"},
    ("en", "ar"): {"hello": "مرحبا", "goodbye": "وداعا", "thank you": "شكرا", "please": "من فضلك", "yes": "نعم", "no": "لا", "good morning": "صباح الخير", "good night": "تصبح على خير", "how are you": "كيف حالك", "welcome": "اهلا"},
    ("en", "pt"): {"hello": "ola", "goodbye": "adeus", "thank you": "obrigado", "please": "por favor", "yes": "sim", "no": "nao", "good morning": "bom dia", "good night": "boa noite", "how are you": "como voce esta", "welcome": "bem vindo"},
    ("en", "ru"): {"hello": "привет", "goodbye": "до свидания", "thank you": "спасибо", "please": "пожалуйста", "yes": "да", "no": "нет", "good morning": "доброе утро", "good night": "спокойной ночи", "how are you": "как дела", "welcome": "добро пожаловать"},
    ("en", "hi"): {"hello": "नमस्ते", "goodbye": "अलविदा", "thank you": "धन्यवाद", "please": "कृपया", "yes": "हाँ", "no": "नहीं", "good morning": "शुभ प्रभात", "good night": "शुभ रात्रि", "how are you": "आप कैसे हैं", "welcome": "स्वागत है"},
    ("en", "tr"): {"hello": "merhaba", "goodbye": "hosca kal", "thank you": "tesekkur ederim", "please": "lutfen", "yes": "evet", "no": "hayir", "good morning": "gunaydin", "good night": "iyi geceler", "how are you": "nasil siniz", "welcome": "hos geldiniz"},
}

LOCALE_FORMATS = {
    "en-US": {"decimal": ".", "thousands": ",", "currency": "$", "currency_pos": "before", "date_short": "MM/DD/YYYY", "date_long": "MMMM D, YYYY", "time": "hh:mm A", "phone": "+1 (XXX) XXX-XXXX"},
    "en-GB": {"decimal": ".", "thousands": ",", "currency": "\u00a3", "currency_pos": "before", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+44 XXXX XXXXXX"},
    "es-ES": {"decimal": ",", "thousands": ".", "currency": "\u20ac", "currency_pos": "after", "date_short": "DD/MM/YYYY", "date_long": "D de MMMM de YYYY", "time": "HH:mm", "phone": "+34 XXX XXX XXX"},
    "fr-FR": {"decimal": ",", "thousands": " ", "currency": "\u20ac", "currency_pos": "after", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+33 X XX XX XX XX"},
    "de-DE": {"decimal": ",", "thousands": ".", "currency": "\u20ac", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D. MMMM YYYY", "time": "HH:mm", "phone": "+49 XXX XXXXXXX"},
    "ja-JP": {"decimal": ".", "thousands": ",", "currency": "\u00a5", "currency_pos": "before", "date_short": "YYYY/MM/DD", "date_long": "YYYY\u5e74M\u6708D\u65e5", "time": "HH:mm", "phone": "+81 XX XXXX XXXX"},
    "zh-CN": {"decimal": ".", "thousands": ",", "currency": "\u00a5", "currency_pos": "before", "date_short": "YYYY-MM-DD", "date_long": "YYYY\u5e74M\u6708D\u65e5", "time": "HH:mm", "phone": "+86 XXX XXXX XXXX"},
    "ko-KR": {"decimal": ".", "thousands": ",", "currency": "\u20a9", "currency_pos": "before", "date_short": "YYYY-MM-DD", "date_long": "YYYY\uB144 MM\uC6D4 DD\uC77C", "time": "HH:mm", "phone": "+82 XX XXXX XXXX"},
    "ar-SA": {"decimal": "\u066b", "thousands": "\u066c", "currency": "\u0631.\u0633", "currency_pos": "after", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "hh:mm", "phone": "+966 XX XXX XXXX"},
    "hi-IN": {"decimal": ".", "thousands": ",", "currency": "\u20b9", "currency_pos": "before", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "hh:mm A", "phone": "+91 XXXXX XXXXX"},
    "pt-BR": {"decimal": ",", "thousands": ".", "currency": "R$", "currency_pos": "before", "date_short": "DD/MM/YYYY", "date_long": "D de MMMM de YYYY", "time": "HH:mm", "phone": "+55 XX XXXXX XXXX"},
    "ru-RU": {"decimal": ",", "thousands": " ", "currency": "\u20bd", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D MMMM YYYY \u0433.", "time": "HH:mm", "phone": "+7 (XXX) XXX-XX-XX"},
    "it-IT": {"decimal": ",", "thousands": ".", "currency": "\u20ac", "currency_pos": "after", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+39 XXX XXX XXXX"},
    "nl-NL": {"decimal": ",", "thousands": ".", "currency": "\u20ac", "currency_pos": "before", "date_short": "DD-MM-YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+31 X XXX XXXX"},
    "pl-PL": {"decimal": ",", "thousands": " ", "currency": "z\u0142", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+48 XXX XXX XXX"},
    "tr-TR": {"decimal": ",", "thousands": ".", "currency": "\u20ba", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+90 (XXX) XXX XX XX"},
    "th-TH": {"decimal": ".", "thousands": ",", "currency": "\u0e3f", "currency_pos": "before", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+66 XX XXX XXXX"},
    "vi-VN": {"decimal": ",", "thousands": ".", "currency": "₫", "currency_pos": "after", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+84 XXX XXX XXXX"},
    "uk-UA": {"decimal": ",", "thousands": " ", "currency": "\u20b4", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+380 XX XXX XX XX"},
    "sv-SE": {"decimal": ",", "thousands": " ", "currency": "kr", "currency_pos": "after", "date_short": "YYYY-MM-DD", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+46 XX XXX XXX XX"},
    "cs-CZ": {"decimal": ",", "thousands": " ", "currency": "K\u010d", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D. MMMM YYYY", "time": "HH:mm", "phone": "+420 XXX XXX XXX"},
    "da-DK": {"decimal": ",", "thousands": ".", "currency": "kr", "currency_pos": "after", "date_short": "DD-MM-YYYY", "date_long": "D. MMMM YYYY", "time": "HH:mm", "phone": "+45 XX XX XX XX"},
    "no-NO": {"decimal": ",", "thousands": " ", "currency": "kr", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D. MMMM YYYY", "time": "HH:mm", "phone": "+47 XXX XX XXX"},
    "fi-FI": {"decimal": ",", "thousands": " ", "currency": "\u20ac", "currency_pos": "after", "date_short": "DD.MM.YYYY", "date_long": "D. MMMMta YYYY", "time": "HH:mm", "phone": "+358 XX XXX XXXX"},
    "el-GR": {"decimal": ",", "thousands": ".", "currency": "\u20ac", "currency_pos": "after", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+30 XXX XXX XXXX"},
    "he-IL": {"decimal": ".", "thousands": ",", "currency": "\u20aa", "currency_pos": "before", "date_short": "DD/MM/YYYY", "date_long": "D \u05d1MMMM YYYY", "time": "HH:mm", "phone": "+972 XX XXX XXXX"},
    "id-ID": {"decimal": ",", "thousands": ".", "currency": "Rp", "currency_pos": "before", "date_short": "DD/MM/YYYY", "date_long": "D MMMM YYYY", "time": "HH:mm", "phone": "+62 XX XXXX XXXX"},
}

PLURAL_RULES = {
    "en": lambda c: "" if c == 1 else "s",
    "es": lambda c: "" if c == 1 else "s",
    "fr": lambda c: "" if c <= 1 else "s",
    "de": lambda c: "" if c == 1 else "n",
    "it": lambda c: "" if c == 1 else "i",
    "pt": lambda c: "" if c == 1 else "s",
    "ru": lambda c: "" if c % 10 == 1 and c % 100 != 11 else ("a" if c % 10 in (2, 3, 4) and c % 100 not in (12, 13, 14) else "ov"),
    "ja": lambda c: "",
    "zh": lambda c: "",
    "ko": lambda c: "",
    "ar": lambda c: "" if c == 0 else ("" if c == 1 else ("n" if c == 2 else "")),
    "hi": lambda c: "" if c == 1 else "",
    "tr": lambda c: "",
    "nl": lambda c: "" if c == 1 else "en",
    "pl": lambda c: "" if c == 1 else ("e" if c % 10 in (2, 3, 4) and c % 100 not in (12, 13, 14) else ""),
    "sv": lambda c: "" if c == 1 else "ar",
    "th": lambda c: "",
    "vi": lambda c: "",
    "uk": lambda c: "" if c % 10 == 1 and c % 100 != 11 else ("i" if c % 10 in (2, 3, 4) and c % 100 not in (12, 13, 14) else ""),
    "el": lambda c: "" if c == 1 else "es",
    "cs": lambda c: "" if c == 1 else ("y" if c in (2, 3, 4) else ""),
    "ro": lambda c: "" if c == 1 else ("e" if c == 0 or (c % 100 >= 10 and c % 100 <= 19) else "i"),
    "he": lambda c: "" if c == 1 else "" if c == 2 else "",
    "id": lambda c: "",
    "ms": lambda c: "",
    "fi": lambda c: "" if c == 1 else "a",
    "da": lambda c: "" if c == 1 else "r",
    "no": lambda c: "" if c == 1 else "r",
}


def _unicode_ranges(text):
    ranges = Counter()
    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A:
            ranges["latin"] += 1
        elif 0x0400 <= cp <= 0x04FF:
            ranges["cyrillic"] += 1
        elif 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
            ranges["arabic"] += 1
        elif 0x0900 <= cp <= 0x097F:
            ranges["devanagari"] += 1
        elif 0x3040 <= cp <= 0x309F:
            ranges["hiragana"] += 1
        elif 0x30A0 <= cp <= 0x30FF:
            ranges["katakana"] += 1
        elif 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            ranges["cjk"] += 1
        elif 0xAC00 <= cp <= 0xD7AF or 0x1100 <= cp <= 0x11FF:
            ranges["hangul"] += 1
        elif 0x0E00 <= cp <= 0x0E7F:
            ranges["thai"] += 1
        elif 0x0370 <= cp <= 0x03FF:
            ranges["greek"] += 1
        elif 0x0590 <= cp <= 0x05FF:
            ranges["hebrew"] += 1
        elif 0x00C0 <= cp <= 0x024F:
            ranges["latin_extended"] += 1
    return ranges


def detect_language(text):
    ranges = _unicode_ranges(text)
    total = sum(ranges.values()) or 1
    words = re.findall(r'\w+', text.lower())
    scores = {}
    for lang_code, lang_words in COMMON_WORDS.items():
        if isinstance(lang_words, set):
            lang_words = list(lang_words)
        score = sum(1 for w in words if w in lang_words)
        scores[lang_code] = score / (len(words) or 1)

    if ranges.get("cjk", 0) > total * 0.3:
        if ranges.get("hiragana", 0) + ranges.get("katakana", 0) > 0:
            return "ja", 0.9, "CJK (Japanese scripts detected)"
        if ranges.get("hangul", 0) > 0:
            return "ko", 0.85, "Hangul detected"
        return "zh", 0.7, "CJK characters (Chinese assumed)"
    if ranges.get("hangul", 0) > total * 0.3:
        return "ko", 0.9, "Hangul detected"
    if ranges.get("thai", 0) > total * 0.3:
        return "th", 0.9, "Thai script"
    if ranges.get("arabic", 0) > total * 0.3:
        return "ar", 0.85, "Arabic script"
    if ranges.get("devanagari", 0) > total * 0.3:
        return "hi", 0.85, "Devanagari script"
    if ranges.get("cyrillic", 0) > total * 0.3:
        best_ru = scores.get("ru", 0)
        best_uk = scores.get("uk", 0)
        if best_uk > best_ru:
            return "uk", 0.7 + best_uk, "Cyrillic + Ukrainian words"
        return "ru", 0.7 + best_ru, "Cyrillic + Russian words"
    if ranges.get("greek", 0) > total * 0.3:
        return "el", 0.85, "Greek script"
    if ranges.get("hebrew", 0) > total * 0.3:
        return "he", 0.85, "Hebrew script"
    if ranges.get("latin", 0) + ranges.get("latin_extended", 0) > total * 0.5:
        best_lang = max(scores, key=scores.get) if scores else "en"
        conf = 0.6 + min(scores.get(best_lang, 0), 0.35)
        return best_lang, conf, f"Latin script, best word match"
    return "en", 0.5, "Default fallback"


def translate_text(text, source, target):
    if source == "auto":
        source, _, _ = detect_language(text)
    key = (source, target)
    rev_key = (target, source)
    if key in TRANSLATION_DICT:
        d = TRANSLATION_DICT[key]
    elif rev_key in TRANSLATION_DICT:
        d = {v: k for k, v in TRANSLATION_DICT[rev_key].items()}
    else:
        return {"translated": text, "note": f"No dictionary for {source}->{target}. Returning original.", "source": source, "target": target}
    lower = text.lower().strip()
    if lower in d:
        return {"translated": d[lower], "source": source, "target": target, "match": "exact"}
    words = lower.split()
    result_words = []
    for w in words:
        result_words.append(d.get(w, w))
    return {"translated": " ".join(result_words), "source": source, "target": target, "match": "partial"}


def localize_text(text, locale):
    fmt = LOCALE_FORMATS.get(locale)
    if not fmt:
        return {"error": f"Unknown locale: {locale}. Available: {list(LOCALE_FORMATS.keys())[:10]}..."}
    nums = re.findall(r'[\d,]+\.?\d*', text)
    result = text
    for num_str in nums:
        try:
            val = float(num_str.replace(fmt.get("thousands", ","), "").replace(fmt.get("decimal", "."), "." if fmt.get("decimal") != "." else "."))
            if "." in num_str:
                formatted = f"{val:,.2f}".replace(",", fmt["thousands"]).replace(".", fmt["decimal"])
            else:
                formatted = f"{int(val):,}".replace(",", fmt["thousands"])
            result = result.replace(num_str, formatted, 1)
        except ValueError:
            pass
    return {"localized": result, "locale": locale, "formats": fmt}


def pluralize_word(word, count, language):
    rule = PLURAL_RULES.get(language, PLURAL_RULES.get("en"))
    suffix = rule(count)
    return {"word": word, "count": count, "language": language, "result": f"{word}{suffix}", "plural": count != 1}


def get_formats(locale):
    fmt = LOCALE_FORMATS.get(locale)
    if not fmt:
        return {"error": f"Unknown locale: {locale}. Available: {sorted(LOCALE_FORMATS.keys())}"}
    return {"locale": locale, "formats": fmt}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-i18n", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_i18n_detect":
                lang, conf, note = detect_language(args["text"])
                result = {"detected": lang, "language": LANGUAGES.get(lang, {}).get("name", lang), "confidence": round(conf, 3), "note": note}
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
            elif name == "ctz_i18n_translate":
                r = translate_text(args["text"], args.get("source", "auto"), args["target"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False)}]}}
            elif name == "ctz_i18n_localize":
                r = localize_text(args["text"], args["locale"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False)}]}}
            elif name == "ctz_i18n_pluralize":
                r = pluralize_word(args["word"], args["count"], args["language"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r)}]}}
            elif name == "ctz_i18n_formats":
                r = get_formats(args["locale"])
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False)}]}}
            elif name == "ctz_i18n_languages":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"languages": LANGUAGES, "count": len(LANGUAGES), "locale_count": len(LOCALE_FORMATS)}, ensure_ascii=False, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r:
                sys.stdout.write(json.dumps(r) + "\n")
                sys.stdout.flush()
        except: pass
