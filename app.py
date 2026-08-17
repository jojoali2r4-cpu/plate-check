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

    # إزالة كل شيء غير عربي أو رقم
    text = re.sub(
        r"[^0-9\u0600-\u06FF]",
        "",
        text
    )

    return text


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
    "جيم": "ج",

    "حاء": "ح",
    "حا": "ح",

    "خاء": "خ",
    "خا": "خ",

    "دال": "د",
    "دال": "د",

    "ذال": "ذ",
    "ذا": "ذ",

    "راء": "ر",
    "را": "ر",

    "زاي": "ز",
    "زاي": "ز",

    "سين": "س",
    "سين": "س",

    "شين": "ش",
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
    "عين": "ع",

    "غين": "غ",
    "غين": "غ",

    "فاء": "ف",
    "فا": "ف",

    "قاف": "ق",
    "قاف": "ق",

    "كاف": "ك",
    "كاف": "ك",

    "لام": "ل",
    "لام": "ل",

    "ميم": "م",
    "ميم": "م",

    "نون": "ن",
    "نون": "ن",

    "هاء": "ه",
    "ها": "ه",

    "واو": "و",
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

    # الأطول أولاً حتى لا يحصل استبدال خاطئ
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
    """
    استخراج الأرقام من النص.
    """

    text = normalize_numbers(text)

    return "".join(
        re.findall(r"\d", text)
    )


# =========================================================
# تجهيز نص اللوحة
# =========================================================

def plate_information(plate):
    """
    يرجع:
    - اللوحة الأصلية
    - الحروف
    - الأرقام
    - النص المنظف
    """

    original = str(plate).strip()

    normalized = clean_text(original)

    digits = "".join(
        re.findall(r"\d", normalized)
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

    # أولاً الاسم المطلوب بالضبط
    if "اللوحه" in df.columns:
        return "اللوحه"

    # احتمالات أخرى
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

    # محاولة اكتشاف أي عمود يحتوي كلمة لوحة
    for column in df.columns:

        column_text = str(column).strip()

        if "لوح" in column_text:
            return column

    return None


# =========================================================
# رفع ملف Excel
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

        plate_column = find_plate_column(df)

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
            )

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء قراءة ملف Excel: {e}"
        )


# =========================================================
# تحويل الصوت إلى WAV خفيف
# =========================================================

def convert_to_wav(audio_bytes):

    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes)
    )

    # Mono
    audio = audio.set_channels(1)

    # 16000 Hz مناسب للتعرف على الكلام
    audio = audio.set_frame_rate(16000)

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

        with sr.AudioFile(wav_file) as source:

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
            f"❌ مشكلة في الاتصال بخدمة التعرف على الصوت: {e}"
        )

        return ""

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء تحويل الصوت إلى نص: {e}"
        )

        return ""


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

    plate_digits = info["digits"]
    plate_letters = info["letters"]

    if not plate_digits:
        return False

    # -----------------------------------------------------
    # تجهيز الكلام المنطوق
    # -----------------------------------------------------

    spoken_text = normalize_numbers(
        spoken_text
    )

    spoken_text = convert_letter_names(
        spoken_text
    )

    spoken_normalized = clean_text(
        spoken_text
    )

    # -----------------------------------------------------
    # شرط أساسي:
    # أرقام اللوحة يجب أن تكون موجودة
    # -----------------------------------------------------

    spoken_digits = extract_digits(
        spoken_normalized
    )

    if plate_digits not in spoken_digits:
        return False

    # -----------------------------------------------------
    # إذا كانت اللوحة بالكامل موجودة في الكلام
    # فهذا أفضل تطابق ممكن
    # -----------------------------------------------------

    if info["normalized"] in spoken_normalized:
        return True

    # -----------------------------------------------------
    # البحث حول أرقام اللوحة
    #
    # مثال:
    # الكلام:
    # "رسق 2434"
    #
    # نأخذ الجزء القريب من 2434
    # -----------------------------------------------------

    digit_pattern = r"[\s\-_]*".join(
        re.escape(d)
        for d in plate_digits
    )

    digit_match = re.search(
        digit_pattern,
        spoken_text
    )

    if not digit_match:
        return False

    start = max(
        0,
        digit_match.start() - 30
    )

    end = min(
        len(spoken_text),
        digit_match.end() + 30
    )

    local_text = spoken_text[
        start:end
    ]

    local_clean = clean_text(
        local_text
    )

    # -----------------------------------------------------
    # استخراج الحروف الموجودة بالقرب من الرقم
    # -----------------------------------------------------

    local_letters = "".join(
        re.findall(
            r"[\u0600-\u06FF]",
            local_clean
        )
    )

    # لا توجد حروف في اللوحة
    if not plate_letters:
        return True

    # -----------------------------------------------------
    # التطابق المباشر
    # -----------------------------------------------------

    if plate_letters in local_letters:
        return True

    # -----------------------------------------------------
    # محاولة معالجة حالة:
    # ر ص ق 2434
    # بدلاً من:
    # رسق 2434
    # -----------------------------------------------------

    compact_letters = local_letters.replace(
        " ",
        ""
    )

    if plate_letters in compact_letters:
        return True

    # -----------------------------------------------------
    # مطابقة مرنة للحروف فقط
    #
    # لا نستخدمها إلا إذا كانت الأرقام صحيحة
    # -----------------------------------------------------

    if len(plate_letters) >= 2:

        # البحث عن تسلسل حروف قريب من طول لوحة الحروف
        n = len(plate_letters)

        for i in range(
            max(1, len(compact_letters) - n + 1)
        ):

            part = compact_letters[
                i:i+n
            ]

            if len(part) != n:
                continue

            same = sum(
                a == b
                for a, b in zip(
                    plate_letters,
                    part
                )
            )

            score = same / n

            # تطابق قوي جداً للحروف
            if score >= 0.80:
                return True

    return False


# =========================================================
# البحث عن اللوحات الموجودة فقط
# =========================================================

def find_matching_plates(
    spoken_text,
    plates
):

    if not spoken_text or not plates:
        return []

    matches = []

    # نمر على اللوحات الموجودة في Excel
    # ونرجع اللوحة الأصلية نفسها
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
# تسجيل من التطبيق
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

            audio_bytes = audio_recorded[
                "bytes"
            ]

            with st.spinner(
                "🎙️ جاري تحليل التسجيل..."
            ):

                spoken_text = audio_to_text(
                    audio_bytes
                )

            if spoken_text:

                matches = find_matching_plates(
                    spoken_text,
                    plates
                )

                st.session_state.matches = (
                    matches
                )

                st.session_state.spoken_text = (
                    spoken_text
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

            # معرف بسيط لمنع إعادة معالجة نفس الملف
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
# تهيئة النتائج
# =========================================================

if "matches" not in st.session_state:

    st.session_state.matches = []


if "spoken_text" not in st.session_state:

    st.session_state.spoken_text = ""


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

    # عرض اللوحات الموجودة فقط
    # بدون أي خيارات أخرى

    for plate in st.session_state.matches:

        st.success(
            f"🚗 {plate} موجودة في الملف"
        )

else:

    if st.session_state.spoken_text:

        st.error(
            "❌ اللوحة المنطوقة غير موجودة في الملف."
        )

    else:

        st.info(
            "🎙️ سجلي أو ارفعي تسجيلًا للبحث عن اللوحة."
        )
