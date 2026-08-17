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
# توحيد الأرقام
# =========================================================

def normalize_numbers(text):

    if text is None:
        return ""

    arabic_numbers = "٠١٢٣٤٥٦٧٨٩"
    english_numbers = "0123456789"

    table = str.maketrans(
        arabic_numbers,
        english_numbers
    )

    return str(text).translate(table)


# =========================================================
# توحيد الحروف العربية
# =========================================================

def normalize_arabic_letters(text):

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
        "ـ": ""
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

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
# أسماء الحروف العربية
# =========================================================

LETTER_NAMES = {

    "الف": "ا",
    "الف": "ا",
    "ألف": "ا",
    "الفه": "ا",

    "باء": "ب",
    "با": "ب",

    "تاء": "ت",
    "تا": "ت",

    "ثاء": "ث",
    "ثا": "ث",

    "جيم": "ج",
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
    "زايه": "ز",

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
    "يا": "ي"
}


# =========================================================
# تحويل أسماء الحروف إلى حروف
# =========================================================

def convert_letter_names(text):

    if not text:
        return ""

    result = normalize_numbers(str(text))

    # نرتب الأطول أولاً
    names = sorted(
        LETTER_NAMES.keys(),
        key=len,
        reverse=True
    )

    for name in names:

        # التعامل مع وجود مسافات أو علامات
        pattern = r"(?<![\u0600-\u06FF])" + re.escape(name) + r"(?![\u0600-\u06FF])"

        result = re.sub(
            pattern,
            " " + LETTER_NAMES[name] + " ",
            result,
            flags=re.IGNORECASE
        )

    return result


# =========================================================
# تحويل الكلمات الرقمية إلى أرقام
# =========================================================

NUMBER_WORDS = {

    "صفر": "0",
    "واحد": "1",
    "واحده": "1",
    "اثنين": "2",
    "اثنان": "2",
    "اتنين": "2",
    "ثلاثه": "3",
    "ثلاثة": "3",
    "اربعه": "4",
    "أربعه": "4",
    "أربعة": "4",
    "خمسه": "5",
    "خمسة": "5",
    "سته": "6",
    "ستة": "6",
    "سبعه": "7",
    "سبعة": "7",
    "ثمانيه": "8",
    "ثمانية": "8",
    "تسعه": "9",
    "تسعة": "9"
}


def convert_number_words(text):

    if not text:
        return ""

    result = str(text)

    for word, number in NUMBER_WORDS.items():

        result = re.sub(
            r"(?<![\u0600-\u06FF])"
            + re.escape(word)
            + r"(?![\u0600-\u06FF])",
            " " + number + " ",
            result
        )

    return result


# =========================================================
# تجهيز الكلام المنطوق
# =========================================================

def prepare_spoken_text(text):

    if not text:
        return ""

    text = normalize_numbers(text)

    text = normalize_arabic_letters(text)

    text = convert_letter_names(text)

    text = convert_number_words(text)

    return text


# =========================================================
# استخراج الأرقام
# =========================================================

def extract_digits(text):

    if not text:
        return ""

    text = normalize_numbers(text)

    return "".join(
        re.findall(r"\d", text)
    )


# =========================================================
# استخراج الحروف العربية
# =========================================================

def extract_letters(text):

    if not text:
        return ""

    return "".join(
        re.findall(
            r"[\u0621-\u064A]",
            text
        )
    )


# =========================================================
# معلومات اللوحة
# =========================================================

def plate_information(plate):

    original = str(plate).strip()

    normalized = clean_text(original)

    digits = extract_digits(normalized)

    letters = extract_letters(
        normalize_arabic_letters(original)
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
        "PLATE",

        "رقم"
    ]

    for name in possible_names:

        if name in df.columns:
            return name

    for column in df.columns:

        column_text = str(
            column
        ).strip().lower()

        if (
            "لوح" in column_text
            or "plate" in column_text
        ):
            return column

    return None


# =========================================================
# رفع Excel
# =========================================================

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"],
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
                "أسماء الأعمدة الموجودة:"
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
            )

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء قراءة Excel: {e}"
        )


# =========================================================
# تحويل الصوت إلى WAV
# =========================================================

def convert_to_wav(audio_bytes):

    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes)
    )

    audio = audio.set_channels(1)

    audio = audio.set_frame_rate(
        16000
    )

    wav_buffer = io.BytesIO()

    audio.export(
        wav_buffer,
        format="wav"
    )

    wav_buffer.seek(0)

    return wav_buffer


# =========================================================
# تحويل الصوت إلى نص
# =========================================================

def audio_to_text(audio_bytes):

    recognizer = sr.Recognizer()

    try:

        wav_file = convert_to_wav(
            audio_bytes
        )

        with sr.AudioFile(
            wav_file
        ) as source:

            # تقليل الضوضاء
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            audio_data = recognizer.record(
                source
            )

        text = recognizer.recognize_google(
            audio_data,
            language="ar-SA"
        )

        return text

    except sr.UnknownValueError:

        return ""

    except sr.RequestError as e:

        st.error(
            f"❌ مشكلة في خدمة التعرف على الصوت: {e}"
        )

        return ""

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء تحويل الصوت إلى نص: {e}"
        )

        return ""


# =========================================================
# مطابقة الأرقام
# =========================================================

def digits_match(
    plate_digits,
    spoken_text
):

    if not plate_digits:
        return False

    spoken_digits = extract_digits(
        spoken_text
    )

    if not spoken_digits:
        return False

    # تطابق مباشر
    if plate_digits in spoken_digits:
        return True

    # -----------------------------------------------------
    # محاولة العثور على نفس الأرقام حتى لو بينها مسافات
    # -----------------------------------------------------

    pattern = r"\D*".join(
        re.escape(d)
        for d in plate_digits
    )

    if re.search(
        pattern,
        spoken_text
    ):
        return True

    return False


# =========================================================
# مطابقة الحروف
# =========================================================

def letters_match(
    plate_letters,
    spoken_text
):

    if not plate_letters:
        return True

    prepared = prepare_spoken_text(
        spoken_text
    )

    # تنظيف الكلام مع الإبقاء على الحروف والأرقام
    cleaned = re.sub(
        r"[^0-9\u0621-\u064A]",
        "",
        prepared
    )

    spoken_letters = extract_letters(
        prepared
    )

    if not spoken_letters:
        return False

    # تطابق مباشر
    if plate_letters in spoken_letters:
        return True

    # -----------------------------------------------------
    # البحث عن تسلسل قريب من حروف اللوحة
    # -----------------------------------------------------

    n = len(plate_letters)

    if len(spoken_letters) < n:
        return False

    for i in range(
        len(spoken_letters) - n + 1
    ):

        part = spoken_letters[
            i:i+n
        ]

        same = sum(
            a == b
            for a, b in zip(
                plate_letters,
                part
            )
        )

        score = same / n

        if score >= 0.80:
            return True

    return False


# =========================================================
# مطابقة لوحة واحدة
# =========================================================

def plate_matches_spoken_text(
    plate,
    spoken_text
):

    if not spoken_text:
        return False

    info = plate_information(
        plate
    )

    plate_digits = info[
        "digits"
    ]

    plate_letters = info[
        "letters"
    ]

    if not plate_digits:
        return False

    prepared = prepare_spoken_text(
        spoken_text
    )

    # -----------------------------------------------------
    # الأرقام شرط أساسي
    # -----------------------------------------------------

    if not digits_match(
        plate_digits,
        prepared
    ):
        return False

    # -----------------------------------------------------
    # إذا لم توجد حروف في اللوحة
    # -----------------------------------------------------

    if not plate_letters:
        return True

    # -----------------------------------------------------
    # مطابقة الحروف
    # -----------------------------------------------------

    if letters_match(
        plate_letters,
        prepared
    ):
        return True

    # -----------------------------------------------------
    # محاولة مطابقة اللوحة كاملة
    # -----------------------------------------------------

    normalized_plate = clean_text(
        plate
    )

    normalized_spoken = clean_text(
        prepared
    )

    if normalized_plate in normalized_spoken:
        return True

    return False


# =========================================================
# البحث عن اللوحات
# =========================================================

def find_matching_plates(
    spoken_text,
    plates
):

    if not spoken_text or not plates:
        return []

    matches = []

    for plate in plates:

        try:

            if plate_matches_spoken_text(
                plate,
                spoken_text
            ):

                matches.append(
                    plate
                )

        except Exception:
            continue

    # إزالة التكرار
    unique_matches = []

    for plate in matches:

        if plate not in unique_matches:

            unique_matches.append(
                plate
            )

    return unique_matches


# =========================================================
# تهيئة Session State
# =========================================================

if "matches" not in st.session_state:

    st.session_state.matches = []


if "spoken_text" not in st.session_state:

    st.session_state.spoken_text = ""


if "processed_audio_id" not in st.session_state:

    st.session_state.processed_audio_id = None


# =========================================================
# واجهة التسجيل
# =========================================================

st.divider()

st.header(
    "🎙️ مصدر التسجيل"
)


tab1, tab2 = st.tabs(
    [
        "🎙️ تسجيل من التطبيق",
        "📁 رفع تسجيل من الجوال"
    ]
)


# =========================================================
# التسجيل من التطبيق
# =========================================================

with tab1:

    audio_recorded = mic_recorder(

        start_prompt="🎙️ بدء التسجيل",

        stop_prompt="⏹️ إيقاف التسجيل",

        just_once=True,

        use_container_width=True,

        key="recorder"

    )

    if audio_recorded is not None:

        if not plates:

            st.warning(
                "⚠️ ارفعي ملف Excel أولاً."
            )

        else:

            audio_bytes = (
                audio_recorded["bytes"]
            )

            with st.spinner(
                "🎙️ جاري تحليل التسجيل..."
            ):

                spoken_text = audio_to_text(
                    audio_bytes
                )

            st.session_state.spoken_text = (
                spoken_text
            )

            if spoken_text:

                matches = find_matching_plates(
                    spoken_text,
                    plates
                )

                st.session_state.matches = (
                    matches
                )

            else:

                st.session_state.matches = []


# =========================================================
# رفع تسجيل من الجوال
# =========================================================

with tab2:

    uploaded_audio = st.file_uploader(

        "📁 اختاري أي ملف صوتي من ملفات الهاتف",

        type=[
            "m4a",
            "mp3",
            "wav",
            "ogg",
            "webm",
            "aac",
            "flac"
        ],

        key="audio_upload"

    )

    if uploaded_audio is not None:

        if not plates:

            st.warning(
                "⚠️ ارفعي ملف Excel أولاً."
            )

        else:

            current_audio_id = (
                uploaded_audio.name,
                uploaded_audio.size
            )

            if st.session_state.get(
                "processed_audio_id"
            ) != current_audio_id:

                audio_bytes = (
                    uploaded_audio.read()
                )

                st.session_state.processed_audio_id = (
                    current_audio_id
                )

                with st.spinner(
                    "🎙️ جاري تحويل التسجيل إلى نص..."
                ):

                    spoken_text = audio_to_text(
                        audio_bytes
                    )

                st.session_state.spoken_text = (
                    spoken_text
                )

                if spoken_text:

                    matches = find_matching_plates(
                        spoken_text,
                        plates
                    )

                    st.session_state.matches = (
                        matches
                    )

                else:

                    st.session_state.matches = []


# =========================================================
# عرض النص الذي فهمه النظام
# =========================================================

if st.session_state.spoken_text:

    st.divider()

    st.subheader(
        "🎧 النص الذي فهمه النظام"
    )

    st.info(
        st.session_state.spoken_text
    )


# =========================================================
# النتائج
# =========================================================

st.divider()

st.header(
    "📋 النتيجة"
)


if st.session_state.matches:

    st.success(
        f"✅ تم العثور على "
        f"{len(st.session_state.matches)} "
        f"لوحة موجودة في الملف."
    )

    for plate in st.session_state.matches:

        st.success(
            f"🚗 {plate} موجودة في الملف"
        )

else:

    if st.session_state.spoken_text:

        st.error(
            "❌ لم يتم العثور على اللوحة المنطوقة في الملف."
        )

    else:

        st.info(
            "🎙️ سجلي أو ارفعي تسجيلًا للبحث عن اللوحة."
        )
