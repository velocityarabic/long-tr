"""
YouTube Long-Form Video Automation - Bilingual English/Turkish Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Turkish translations
CATEGORIES_TURKISH = {
    "Motivation": "Motivasyon",
    "Love": "Aşk",
    "Success": "Başarı",
    "Wisdom": "Bilgelik",
    "Happiness": "Mutluluk",
    "Self Improvement": "Kendini Geliştirme",
    "Gratitude": "Şükran",
    "Friendship": "Arkadaşlık",
    "Hope": "Umut",
    "Creativity": "Yaratıcılık",
    "Inner Peace": "İç Huzur",
    "Confidence": "Özgüven",
    "Perseverance": "Azim",
    "Inspiration": "İlham",
    "Positive Life": "Pozitif Yaşam",
    "Courage": "Cesaret",
    "Kindness": "Nezaket",
    "Patience": "Sabır",
    "Forgiveness": "Affetmek",
    "Strength": "Güç",
    "Joy": "Neşe",
    "Balance": "Denge",
    "Growth": "Gelişim",
    "Purpose": "Amaç",
    "Mindfulness": "Farkındalık",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "tr-TR-EmelNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "turkish": phrase["turkish"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_turkish = CATEGORIES_TURKISH[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Turkish.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - STRICTLY ENFORCE:
The "english" field must contain PURE ENGLISH words only. ZERO Turkish/Special Characters.
The "turkish" field contains the Turkish translation in Turkish.
The "pronunciation" field is phonetic English spelling.

WRONG (mixed language): {{"english": "Kendine inan on yourself, believe in yourself", ...}}
WRONG (Turkish in english): {{"english": "Follow your hayal and success will come", ...}}
CORRECT: {{"english": "Make your dreams come true, believe in yourself.", "turkish": "Hayallerini gerçekleştir, kendine inan.", "pronunciation": "ha-ya-lle-ri-ni ger-chek-lesh-tir, ken-di-ne i-nan."}}

The english field MUST be 100% English words only. NO Turkish words allowed.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Turkish) with commas for natural pauses
2. Turkish translation (Turkish only)
3. Pronunciation guide (phonetic English spelling)
CRITICAL: Every translation MUST be in Turkish. NEVER use German, Spanish, or any other language. Only Turkish.

Return as JSON array:
[{{"english": "...", "turkish": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Turkish teacher. CRITICAL: The 'english' field must contain PURE ENGLISH words ONLY. NO Turkish in english field. Turkish goes in the 'turkish' field. This is strictly enforced."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "turkish": "Kendine inan.", "pronunciation": "ken-di-ne i-nan."},
            {"english": "You are capable of amazing things.", "turkish": "İnanılmaz şeyler yapabilirsin.", "pronunciation": "i-na-nil-maz shey-ler ya-pa-bi-lir-sin."},
            {"english": "Dream big, start small.", "turkish": "Büyük hayal et, küçük başla.", "pronunciation": "bu-yuk ha-yal et, ku-chuk bash-la."},
            {"english": "Your future is created by your actions.", "turkish": "Geleceğin eylemlerinle şekillenir.", "pronunciation": "ge-le-ce-in ey-lem-le-rin-le she-kil-le-nir."},
            {"english": "Never give up on your dreams.", "turkish": "Hayallerinden asla vazgeçme.", "pronunciation": "ha-yal-le-rin-den as-la vaz-gesh-me."},
            {"english": "Small steps lead to big changes.", "turkish": "Küçük adımlar büyük değişimlere yol açar.", "pronunciation": "ku-chuk a-dum-lar bu-yuk de-i-shim-le-re yol a-char."},
            {"english": "You are stronger than you think.", "turkish": "Düşündüğünden daha güçlüsün.", "pronunciation": "du-shun-du-un-den da-ha guch-lu-sun."},
        ],
        "Love": [
            {"english": "Love yourself first.", "turkish": "Önce kendini sev.", "pronunciation": "on-ce ken-di-ni sev."},
            {"english": "Love makes everything possible.", "turkish": "Sevgi her şeyi mümkün kılar.", "pronunciation": "sev-gi her she-yi mum-kun ku-lar."},
            {"english": "My heart beats for you.", "turkish": "Kalbim senin için atıyor.", "pronunciation": "kal-bim se-nin i-chin a-tu-yor."},
            {"english": "You are my everything.", "turkish": "Sen benim her şeyimsin.", "pronunciation": "sen be-nim her shey-im-sin."},
            {"english": "Together forever, hand in hand.", "turkish": "Sonsuza kadar el ele.", "pronunciation": "son-su-za ka-dar el e-le."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "turkish": "Başarı sıkı çalışmadan gelir.", "pronunciation": "ba-sha-ru sı-kı cha-lush-ma-dan ge-lir."},
            {"english": "Keep going, you're getting there.", "turkish": "Devam et, neredeyse geldin.", "pronunciation": "de-vam et, ne-re-dey-se gel-din."},
            {"english": "Winners never quit.", "turkish": "Kazananlar asla pes etmez.", "pronunciation": "ka-za-nan-lar as-la pes et-mez."},
            {"english": "Your effort will pay off.", "turkish": "Çabanın karşılığını alacaksın.", "pronunciation": "cha-ba-nun kar-shu-lu-u-nu a-la-jak-sun."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "turkish": "Bilgi güçtür.", "pronunciation": "bil-gi guch-tur."},
            {"english": "Learn from yesterday, live for today.", "turkish": "Dünden öğren, bugün için yaşa.", "pronunciation": "dun-den or-en, bu-gun i-chin ya-sha."},
            {"english": "Think before you act.", "turkish": "Harekete geçmeden önce düşün.", "pronunciation": "ha-re-ke-te gech-me-den on-ce du-shun."},
            {"english": "Experience is the best teacher.", "turkish": "Deneyim en iyi öğretmendir.", "pronunciation": "de-ne-yim en i-yi or-ret-men-dir."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "turkish": "Mutluluk bir seçimdir.", "pronunciation": "mut-lu-luk bir se-chim-dir."},
            {"english": "Find joy in the little things.", "turkish": "Küçük şeylerde neşe bul.", "pronunciation": "ku-chuk shey-ler-de ne-she bul."},
            {"english": "Smile, it makes others happy.", "turkish": "Gülümse, bu başkalarını mutlu eder.", "pronunciation": "gu-lum-se, bu bash-ka-la-ru-nu mut-lu e-der."},
            {"english": "Today is a gift.", "turkish": "Bugün bir hediyedir.", "pronunciation": "bu-gun bir he-di-ye-dir."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "turkish": "Dünden daha iyi ol.", "pronunciation": "dun-den da-ha i-yi ol."},
            {"english": "Grow through what you go through.", "turkish": "Yaşadıklarından büyü.", "pronunciation": "ya-sha-duk-la-run-dan bu-yu."},
            {"english": "Invest in yourself daily.", "turkish": "Her gün kendine yatırım yap.", "pronunciation": "her gun ken-di-ne ya-tu-rum yap."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "turkish": "Her şey için teşekkür ederim.", "pronunciation": "her shey i-chin te-shek-kur e-de-rim."},
            {"english": "I appreciate your help.", "turkish": "Yardımını takdir ediyorum.", "pronunciation": "yar-du-mu-nu tak-dir e-di-yo-rum."},
            {"english": "Grateful for this moment.", "turkish": "Bu an için minnettarım.", "pronunciation": "bu an i-chin min-net-ta-rum."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "turkish": "Ne olursa olsun sonsuza kadar arkadaş.", "pronunciation": "ne o-lur-sa ol-sun son-su-za ka-dar ar-ka-dash."},
            {"english": "You are my best friend.", "turkish": "Sen benim en iyi arkadaşımsın.", "pronunciation": "sen be-nim en i-yi ar-ka-da-shum-sun."},
            {"english": "True friends stick together.", "turkish": "Gerçek arkadaşlar birlikte kalır.", "pronunciation": "ger-chek ar-ka-dash-lar bir-lik-te ka-lur."},
        ],
        "Hope": [
            {"english": "There is always hope.", "turkish": "Her zaman umut vardır.", "pronunciation": "her za-man u-mut var-dur."},
            {"english": "Better days are coming.", "turkish": "Daha güzel günler geliyor.", "pronunciation": "da-ha gu-zel gun-ler ge-li-yor."},
            {"english": "Keep faith, keep going.", "turkish": "İnancını koru, devam et.", "pronunciation": "i-nan-ju-nu ko-ru, de-vam et."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "turkish": "Bugün güzel bir şey yarat.", "pronunciation": "bu-gun gu-zel bir shey ya-rat."},
            {"english": "Your imagination is unlimited.", "turkish": "Hayal gücün sınırsız.", "pronunciation": "ha-yal gu-chun sun-ruz-suz."},
            {"english": "Art comes from the heart.", "turkish": "Sanat kalpten gelir.", "pronunciation": "sa-nat kalp-ten ge-lir."},
            {"english": "Express yourself freely.", "turkish": "Kendini özgürce ifade et.", "pronunciation": "ken-di-ni oz-gur-ce i-fa-de et."},
            {"english": "Innovation starts with curiosity.", "turkish": "Yenilik merakla başlar.", "pronunciation": "ye-ni-lik me-rak-la bash-lar."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "turkish": "Kendi içinde huzur bul.", "pronunciation": "ken-di i-chin-de hu-zur bul."},
            {"english": "Breathe, relax, let go.", "turkish": "Nefes al, rahatla, bırak git.", "pronunciation": "ne-fes al, ra-hat-la, bu-rak git."},
            {"english": "Calm mind, happy heart.", "turkish": "Sakin zihin, mutlu kalp.", "pronunciation": "sa-kin zi-hin, mut-lu kalp."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "turkish": "Olduğun gibi yeterlisin.", "pronunciation": "ol-du-un gi-bi ye-ter-li-sin."},
            {"english": "Stand tall, speak up.", "turkish": "Dik dur, sesini yükselt.", "pronunciation": "dik dur, se-si-ni yuk-selt."},
            {"english": "Believe in your abilities.", "turkish": "Yeteneklerine güven.", "pronunciation": "ye-te-nek-le-ri-ne gu-ven."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "turkish": "Asla pes etme, devam et.", "pronunciation": "as-la pes et-me, de-vam et."},
            {"english": "Storms make trees take deeper roots.", "turkish": "Fırtınalar ağaçların köklerini derinleştirir.", "pronunciation": "fur-tu-na-lar a-ach-la-run kok-le-ri-ni de-rin-lesh-ti-rir."},
            {"english": "Patience and persistence win.", "turkish": "Sabır ve azim kazanır.", "pronunciation": "sa-bur ve a-zim ka-za-nur."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "turkish": "Işığın parlak parlasın.", "pronunciation": "i-shu-un par-lak par-la-sun."},
            {"english": "Inspire others by your actions.", "turkish": "Başkalarına eylemlerinle ilham ver.", "pronunciation": "bash-ka-la-ru-na ey-lem-le-rin-le il-ham ver."},
            {"english": "Be the change you want to see.", "turkish": "Görmek istediğin değişim ol.", "pronunciation": "gor-mek is-te-di-in de-i-shim ol."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "turkish": "Her gün pozitifliği seç.", "pronunciation": "her gun po-zi-tif-li-i sech."},
            {"english": "Good vibes only.", "turkish": "Sadece iyi enerji.", "pronunciation": "sa-de-ce i-yi e-ner-ji."},
            {"english": "Life is what you make it.", "turkish": "Hayat senin ona kattığın gibidir.", "pronunciation": "ha-yat se-nin o-na kat-tu-un gi-bi-dir."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "turkish": "Cesur ol, ilk adımı at.", "pronunciation": "ce-sur ol, ilk a-du-mu at."},
            {"english": "Courage is not the absence of fear.", "turkish": "Cesaret korkunun yokluğu değildir.", "pronunciation": "ce-sa-ret kor-ku-nun yok-lu-u de-i-l-dir."},
            {"english": "Face your fears head on.", "turkish": "Korkularınla yüzleş.", "pronunciation": "kor-ku-la-run-la yuz-lesh."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "turkish": "Tanıştığın herkese nazik ol.", "pronunciation": "ta-nush-tu-un her-ke-se na-zik ol."},
            {"english": "Kindness costs nothing, means everything.", "turkish": "Nezaket hiçbir şeye mal olmaz, her şey demektir.", "pronunciation": "ne-za-ket hich-bir she-ye mal ol-maz, her shey de-mek-tir."},
            {"english": "Spread kindness wherever you go.", "turkish": "Gittiğin her yerde nezaket saç.", "pronunciation": "git-ti-in her yer-de ne-za-ket sach."},
        ],
        "Patience": [
            {"english": "Good things take time.", "turkish": "Güzel şeyler zaman alır.", "pronunciation": "gu-zel shey-ler za-man a-lur."},
            {"english": "Wait patiently, trust the process.", "turkish": "Sabırla bekle, sürece güven.", "pronunciation": "sa-bur-la bek-le, su-re-ce gu-ven."},
            {"english": "Rome wasn't built in a day.", "turkish": "Roma bir günde inşa edilmedi.", "pronunciation": "ro-ma bir gun-de in-sha e-dil-me-di."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "turkish": "Affet ve kendini özgür bırak.", "pronunciation": "af-fet ve ken-di-ni oz-gur bu-rak."},
            {"english": "Let go of grudges, find peace.", "turkish": "Küskünlükleri bırak, huzur bul.", "pronunciation": "kus-kun-luk-le-ri bu-rak, hu-zur bul."},
            {"english": "Forgiveness is a gift to yourself.", "turkish": "Affetmek kendine bir hediyedir.", "pronunciation": "af-fet-mek ken-di-ne bir he-di-ye-dir."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "turkish": "Bildiğinden daha güçlüsün.", "pronunciation": "bil-di-in-den da-ha guch-lu-sun."},
            {"english": "Inner strength comes from within.", "turkish": "İçsel güç içeriden gelir.", "pronunciation": "ich-sel guch i-che-ri-den ge-lir."},
            {"english": "Challenges make you stronger.", "turkish": "Zorluklar seni daha güçlü yapar.", "pronunciation": "zor-luk-lar se-ni da-ha guch-lu ya-par."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "turkish": "Her anda neşe bul.", "pronunciation": "her an-da ne-she bul."},
            {"english": "Joy is contagious, spread it.", "turkish": "Neşe bulaşıcıdır, yay onu.", "pronunciation": "ne-she bu-la-shu-cu-dur, yay o-nu."},
            {"english": "Dance like nobody's watching.", "turkish": "Kimse izlemiyormuş gibi dans et.", "pronunciation": "kim-se iz-le-mi-yor-mush gi-bi dans et."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "turkish": "Hayatında denge bul.", "pronunciation": "ha-ya-tun-da den-ge bul."},
            {"english": "Work hard, rest well.", "turkish": "Sıkı çalış, iyi dinlen.", "pronunciation": "sı-kı cha-lush, i-yi din-len."},
            {"english": "Too much of anything is not good.", "turkish": "Her şeyin fazlası zarardır.", "pronunciation": "her she-yin faz-la-sı za-rar-dur."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "turkish": "Gelişim konfor alanının dışında olur.", "pronunciation": "ge-li-shim kon-for a-la-nu-nun du-shun-da o-lur."},
            {"english": "Embrace change, grow stronger.", "turkish": "Değişimi kucakla, daha güçlü büyü.", "pronunciation": "de-i-shi-mi ku-jak-la, da-ha guch-lu bu-yu."},
            {"english": "Every challenge is a chance to grow.", "turkish": "Her zorluk büyümek için bir fırsattır.", "pronunciation": "her zor-luk bu-yu-mek i-chin bir fur-sat-tur."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "turkish": "Amacını bul, onu takip et.", "pronunciation": "a-ma-ju-nu bul, o-nu ta-kip et."},
            {"english": "Your life has meaning.", "turkish": "Hayatının bir anlamı var.", "pronunciation": "ha-ya-tu-nun bir an-la-mu var."},
            {"english": "Live with intention, not accident.", "turkish": "Niyetle yaşa, tesadüfen değil.", "pronunciation": "ni-yet-le ya-sha, te-sa-du-fen de-il."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "turkish": "Bu anda var ol.", "pronunciation": "bu an-da var ol."},
            {"english": "Breathe deeply, stay grounded.", "turkish": "Derin nefes al, topraklanmış kal.", "pronunciation": "de-rin ne-fes al, top-rak-lan-mush kal."},
            {"english": "Notice the little things around you.", "turkish": "Etrafındaki küçük şeyleri fark et.", "pronunciation": "et-ra-fun-da-ki ku-chuk shey-le-ri fark et."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["turkish"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    turkish = phrase_data.get("turkish", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(turkish, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Turkish Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY TURKISH"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_turkish: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER TURKISH", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_turkish, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ÖNEMLİ İFADE"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY TURKISH", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_turkish: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Turkish in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_turkish})",
        f"60 Turkish Phrases for {category_english} | Speak Turkish Like a Native! ({category_turkish})",
        f"Master Turkish {category_english} | 60 Essential Turkish Phrases with Pronunciation | Velocity Turkish",
        f"Turkish Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Turkish Fluently | {category_english} Phrases | English + Turkish + Pronunciation",
    ]

    description = f"""🇹🇷 Learn Turkish with Velocity Turkish! 🇹🇷

In this video, you'll learn 60 essential Turkish phrases about {category_english} ({category_turkish}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Turkish
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Turkish: {phrase['turkish']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Turkish beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Turkish language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Turkish learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY TURKISH:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Turkish Motivation Phrases
• Turkish Love Expressions
• Basic Turkish Greetings

#LearnTurkish #TurkishPhrases #TurkishLanguage #{category_english.replace(' ', '')} #VelocityTurkish #TurkishForBeginners #SpeakTurkish #TurkishVocabulary #Pronunciation #LanguageLearning #Turkish101 #TurkishLesson

---
© Velocity Turkish - Making Turkish learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Turkish",
            "Turkish Phrases",
            "Turkish Language",
            category_english,
            "Velocity Turkish",
            "Turkish for Beginners",
            "Speak Turkish",
            "Turkish Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Turkish 101",
            "Turkish Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_turkish": category_turkish,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_TURKISH[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['turkish']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_TURKISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_TURKISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_TURKISH[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Turkish: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Turkish", "Turkish Phrases", "Turkish", category_english, "Velocity Turkish"],
        "category_english": category_english,
        "category_turkish": CATEGORIES_TURKISH[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Turkish")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Turkish YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY TURKISH - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_TURKISH[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)