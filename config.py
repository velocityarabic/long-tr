"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY TURKISH"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "TURKISH"
HANDLE = "@velocityturkish"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'tr',
 'name': 'Turkish',
 'native_name': 'Türkçe',
 'history_key': 'turkish',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'tr-TR-EmelNeural',
 'native_fallback_voice': 'tr-TR-AhmetNeural',
 'native_engine': 'edge',
 'native_lang_code': 'tr',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'TÜRKÇE',
 'translit_label': 'SAY IT LIKE',
 'flag': 'tr',
 'greeting': 'Merhaba!',
 'encouragement': 'Harika!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÇĞİÖŞÜçğıöşü'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motivasyon',
 'Love': 'Aşk',
 'Success': 'Başarı',
 'Wisdom': 'Bilgelik',
 'Happiness': 'Mutluluk',
 'Self Improvement': 'Kendini Geliştirme',
 'Gratitude': 'Şükran',
 'Friendship': 'Arkadaşlık',
 'Hope': 'Umut',
 'Creativity': 'Yaratıcılık',
 'Inner Peace': 'İç Huzur',
 'Confidence': 'Özgüven',
 'Perseverance': 'Azim',
 'Inspiration': 'İlham',
 'Positive Life': 'Pozitif Yaşam',
 'Courage': 'Cesaret',
 'Kindness': 'Nezaket',
 'Patience': 'Sabır',
 'Forgiveness': 'Affetmek',
 'Strength': 'Güç',
 'Joy': 'Neşe',
 'Balance': 'Denge',
 'Growth': 'Gelişim',
 'Purpose': 'Amaç',
 'Mindfulness': 'Farkındalık',
 'Travel & Airport': 'Seyahat ve Havaalanı',
 'Ordering Food & Dining': 'Yemek Siparişi ve Restoran',
 'Shopping & Prices': 'Alışveriş ve Fiyatlar',
 'Asking for Directions': 'Yol Tarifi Sorma',
 'Hotel & Accommodation': 'Otel ve Konaklama',
 'Daily Routine': 'Günlük Rutin',
 'Meeting People & Greetings': 'İnsanlarla Tanışma ve Selamlaşma',
 'Emergency & Health': 'Acil Durum ve Sağlık',
 'Public Transportation': 'Toplu Taşıma',
 'Work & Office': 'İş ve Ofis',
 'Weather & Small Talk': 'Hava Durumu ve Sohbet',
 'Coffee Shop & Bakery': 'Kafeterya ve Pastane',
 'Family & Home': 'Aile ve Ev',
 'Hobbies & Free Time': 'Hobiler ve Boş Zaman',
 'Dating & Romance': 'Flört ve Romantizm',
 'Phone Calls & Messages': 'Telefon Görüşmeleri ve Mesajlar',
 'Banking & Money': 'Banka ve Para',
 'Doctor & Pharmacy': 'Doktor ve Eczane',
 'Sports & Fitness': 'Spor ve Fitness',
 'Celebrations & Parties': 'Kutlamalar ve Partiler',
 'Feelings & Emotions': 'Duygular',
 'Agreeing & Disagreeing': 'Katılma ve Katılmama',
 'Making Plans': 'Plan Yapma',
 'Common Native Slang': 'Yaygın Argo Kelimeler',
 'Cultural Traditions': 'Kültürel Gelenekler'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnturkish',
 '#turkishlessons',
 '#turkishforbeginners',
 '#languagelearning',
 '#turkishvocabulary',
 '#velocityturkish',
 '#dailyturkish',
 '#turkish',
 '#learnlanguages',
 '#speakturkish']
# ==== HASHTAGS END ====
