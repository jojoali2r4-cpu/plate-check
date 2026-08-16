import streamlit as st
import pandas as pd
import speech_recognition as sr
import re
import io

from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment


# =========================================================
# إعداد الصفحة
# =========================================================

st.set_page_config(
    page_title="نظام فحص لوحات السيارات",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 نظام فحص لوحات السيارات")


# =========================================================
# دوال تنظيف وتوحيد النص
# =========================================================

def normalize_numbers(text):
    """تحويل الأرقام العربية إلى إنجليزية."""

    if text is None:
        return ""

    arabic_numbers = "٠١٢٣٤٥٦٧٨٩"
    english_numbers = "0123456789"

    table = str.maketrans(
        arabic_numbers,
        english_numbers
    )

    return str(text).translate(table)


def normalize_arabic_letters(text):
    """
    توحيد بعض أشكال الحروف العربية
    حتى لا يختلف التطابق بسبب طريقة الكتابة.
    """

    if text is None:
        return ""

    text = str(text).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",

        "ى": "ي",

        "ؤ": "و",
        "ئ": "ي",

        "ة": "ه",

        "ـ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def clean_text(text):
    """
    تنظيف النص:
    - توحيد الأرقام
    - توحيد الحروف
    - إزالة المسافات والعلامات
    """

    if text is None:
        return ""

    text = normalize_numbers(text)
    text = normalize_arabic_letters(text)

    text = re.sub(
        r"[^0-9\u0600-\u06FF]",
        "",
        text
    )

    return text


# =========================================================
# تطبيع اللوحة
# =========================================================

def normalize_plate(plate):

    if plate is None:
        return ""

    plate = normalize_numbers(
        str(plate)
    )

    plate = normalize_arabic_letters(
        plate
    )

    plate = re.sub(
        r"[\s\-_,.!؟،:؛/\\]+",
        "",
        plate
    )

    return plate.strip()


# =========================================================
# تحويل أسماء الحروف العربية التي قد يفهمها Google
# =========================================================

LETTER_NAMES = {
    "الف": "ا",
    "ألف": "ا",

    "باء": "ب",
    "با": "ب",

    "تاء": "ت",
    "تا": "ت",

    "ثاء": "ث",
    "ثا": "ث",

    "جيم": "ج",

    "حاء": "ح",
    "حا": "ح",

    "خاء": "خ",
    "خا": "خ",

    "دال": "د",

    "ذال": "ذ",
    "ذا": "ذ",

    "راء": "ر",
    "را": "ر",

    "زاي": "ز",

    "سين": "س",

    "شين": "ش",

    "صاد": "ص",
    "صا": "ص",

    "ضاد": "ض",
    "ضا": "ض",

    "طاء": "ط",
    "طا": "ط",

    "ظاء": "ظ",
    "ظا": "ظ",

    "عين": "ع",

    "غين": "غ",

    "فاء": "ف",
    "فا": "ف",

    "قاف": "ق",

    "كاف": "ك",

    "لام": "ل",

    "ميم": "م",

    "نون": "ن",

    "هاء": "ه",
    "ها": "ه",

    "واو": "و",

    "ياء": "ي",
    "يا": "ي",
}


def convert_letter_names(text):
    """
    تحويل:
    راء صاد قاف 2434
    إلى:
    ر ص ق 2434
    """

    if not text:
        return ""

    result = str(text)

    names = sorted(
        LETTER_NAMES.keys(),
        key=len,
        reverse=True
    )

    for name in names:

        result = re.sub(
            r"\b" + re.escape(name) + r"\b",
            LETTER_NAMES[name],
            result,
            flags=re.IGNORECASE
        )

    return result


# =========================================================
# استخراج الأرقام
# =========================================================

def extract_digits(text):

    text = normalize_numbers(text)

    return "".join(
        re.findall(
            r"\d",
            text
        )
    )


# =========================================================
# تجهيز نص اللوحة
# =========================================================

def plate_information(plate):

    original = str(
        plate
    ).strip()

    normalized = clean_text(
        original
    )

    digits = "".join(
        re.findall(
            r"\d",
            normalized
        )
    )

    letters = "".join(
        re.findall(
            r"[\u0600-\u06FF]",
            normalized
        )
    )

    return {
        "original": original,
        "normalized": normalized,
        "digits": digits,
        "letters": letters
    }


# =========================================================
# إيجاد عمود اللوحات
# =========================================================

def find_plate_column(df):

    if "اللوحه" in df.columns:

        return "اللوحه"

    possible_names = [
        "اللوحة",
        "لوحه",
        "لوحة",
        "رقم اللوحه",
        "رقم اللوحة",
        "plate",
        "Plate",
        "PLATE"
    ]

    for name in possible_names:

        if name in df.columns:

            return name

    for column in df.columns:

        column_text = str(
            column
        ).strip()

        if "لوح" in column_text:

            return column

    return None


# =========================================================
# رفع ملف Excel
# =========================================================

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=[
        "xlsx",
        "xls"
    ],
    key="excel_file"
)


plates = []


if uploaded_file is not None:

    try:

        df = pd.read_excel(
            uploaded_file
        )

        plate_column = find_plate_column(
            df
        )

        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود اللوحات في ملف Excel."
            )

            st.write(
                "أسماء الأعمدة الموجودة في الملف:"
            )

            st.write(
                list(df.columns)
            )

        else:

            plates = (
                df[plate_column]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            plates = [
                plate
                for plate in plates
                if plate
            ]

            st.success(
                f"✅ تم تحميل {len(plates)} لوحة بنجاح."
