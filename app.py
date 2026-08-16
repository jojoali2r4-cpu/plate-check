import streamlit as st
import pandas as pd
import whisper
import re
import io
import os
import tempfile

from pydub import AudioSegment
from streamlit_mic_recorder import mic_recorder


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
# الإعدادات
# =========================================================

MAX_RECORD_SECONDS = 180

# موديل Whisper
# turbo سريع ودقيق نسبيًا ويدعم العربية
WHISPER_MODEL = "turbo"


# =========================================================
# تحميل Whisper مرة واحدة فقط
# =========================================================

@st.cache_resource
def load_whisper_model():

    model = whisper.load_model(
        WHISPER_MODEL
    )

    return model


# =========================================================
# تطبيع الأرقام
# =========================================================

def normalize_numbers(text):

    if not text:
        return ""

    table = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789"
    )

    return str(text).translate(table)


# =========================================================
# تطبيع الحروف العربية
# =========================================================

def normalize_arabic_letters(text):

    if not text:
        return ""

    replacements = {

        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",

        "ى": "ي",

        "ة": "ه",

        "ؤ": "و",

        "ئ": "ي",

    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    return text


# =========================================================
# تنظيف النص
# =========================================================

def clean_word(word):

    if not word:
        return ""

    word = normalize_numbers(
        word
    )

    word = normalize_arabic_letters(
        word
    )

    word = word.lower().strip()

    word = re.sub(
        r"[^\w\u0600-\u06FF]",
        "",
        word
    )

    return word


# =========================================================
# أسماء الحروف
# =========================================================

LETTER_NAMES = {

    "الف": "ا",
    "الفا": "ا",
    "الف": "ا",

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
    "دا": "د",

    "ذال": "ذ",
    "ذا": "ذ",

    "راء": "ر",
    "را": "ر",

    "زاي": "ز",
    "زايه": "ز",
    "زا": "ز",

    "سين": "س",
    "سا": "س",

    "شين": "ش",
    "شا": "ش",

    "صاد": "ص",
    "صا": "ص",

    "ضاد": "ض",
    "ضا": "ض",

    "طاء": "ط",
    "طا": "ط",

    "ظاء": "ظ",
    "ظا": "ظ",

    "عين": "ع",
    "عا": "ع",

    "غين": "غ",
    "غا": "غ",

    "فاء": "ف",
    "فا": "ف",

    "قاف": "ق",
    "قا": "ق",

    "كاف": "ك",
    "كا": "ك",

    "لام": "ل",
    "لا": "ل",

    "ميم": "م",
    "ما": "م",

    "نون": "ن",
    "نا": "ن",

    "هاء": "ه",
    "ها": "ه",

    "واو": "و",
    "وا": "و",

    "ياء": "ي",
    "يا": "ي",
}


# =========================================================
# أسماء الأرقام
# =========================================================

NUMBER_WORDS = {

    "صفر": "0",

    "واحد": "1",
    "واحدة": "1",
    "واحده": "1",

    "اثنان": "2",
    "اثنين": "2",
    "اثنتين": "2",
    "اتنين": "2",
    "اتنان": "2",

    "ثلاث": "3",
    "ثلاثة": "3",
    "ثلاثه": "3",
    "تلات": "3",
    "تلاتة": "3",
    "تلاته": "3",

    "اربعة": "4",
    "أربعة": "4",
    "اربعه": "4",
    "أربعه": "4",

    "خمسة": "5",
    "خمسه": "5",

    "ست": "6",
    "ستة": "6",
    "سته": "6",

    "سبعة": "7",
    "سبعه": "7",

    "ثمانية": "8",
    "ثمانيه": "8",
    "تمانية": "8",
    "تمانيه": "8",

    "تسعة": "9",
    "تسعه": "9",
}


# =========================================================
# كلمات لا نريد اعتبارها حروف
# =========================================================

IGNORE_WORDS = {

    "لوحة",
    "اللوحة",
    "لوحه",
    "اللوحه",

    "لوحات",

    "رقم",
    "الرقم",
    "رقمه",
    "رقمها",

    "سيارة",
    "سياره",

    "العربية",
    "العربيه",

    "عربية",
    "عربيه",
}


# =========================================================
# تحويل كلمة إلى حرف
# =========================================================

def word_to_letter(word):

    word = clean_word(
        word
    )

    if word in LETTER_NAMES:

        return LETTER_NAMES[word]

    # حرف مكتوب منفرد
    if re.fullmatch(
        r"[ا-ي]",
        word
    ):

        return word

    return None


# =========================================================
# تحويل كلمة إلى رقم
# =========================================================

def word_to_digit(word):

    word = clean_word(
        word
    )

    if word in NUMBER_WORDS:

        return NUMBER_WORDS[word]

    if re.fullmatch(
        r"\d",
        word
    ):

        return word

    return None


# =========================================================
# تطبيع لوحة Excel
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
        r"\s+",
        "",
        plate
    )

    plate = re.sub(
        r"[-_,.!؟،:؛/\\]+",
        "",
        plate
    )

    return plate.strip()


# =========================================================
# استخراج 3 حروف + 4 أرقام
# =========================================================

def get_plate_parts(plate):

    normalized = normalize_plate(
        plate
    )

    letters = "".join(
        re.findall(
            r"[^\W\d_]",
            normalized,
            flags=re.UNICODE
        )
    )

    numbers = "".join(
        re.findall(
            r"\d",
            normalized
        )
    )

    if (
        len(letters) == 3
        and
        len(numbers) == 4
    ):

        return (
            letters,
            numbers
        )

    return (
        None,
        None
    )


# =========================================================
# تجهيز لوحات Excel
# =========================================================

def prepare_excel_plates(plates):

    result = []

    for plate in plates:

        letters, numbers = (
            get_plate_parts(
                plate
            )
        )

        if (
            letters
            and
            numbers
        ):

            result.append({

                "original":
                    str(plate).strip(),

                "letters":
                    letters,

                "numbers":
                    numbers,

                "normalized":
                    normalize_plate(
                        plate
                    )

            })

    return result


# =========================================================
# تحويل الصوت إلى WAV
# =========================================================

def audio_bytes_to_wav(
    audio_bytes
):

    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes)
    )

    audio = audio.set_channels(
        1
    )

    audio = audio.set_frame_rate(
        16000
    )

    # =====================================================
    # الحد الأقصى 3 دقائق
    # =====================================================

    max_ms = (
        MAX_RECORD_SECONDS
        * 1000
    )

    if len(audio) > max_ms:

        audio = audio[:max_ms]

    wav_buffer = io.BytesIO()

    audio.export(
        wav_buffer,
        format="wav"
    )

    wav_buffer.seek(0)

    return wav_buffer


# =========================================================
# Whisper transcription
# =========================================================

def transcribe_audio(
    audio_bytes
):

    try:

        model = load_whisper_model()

        wav_buffer = (
            audio_bytes_to_wav(
                audio_bytes
            )
        )

        # ملف مؤقت
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as tmp:

            tmp.write(
                wav_buffer.read()
            )

            temp_path = tmp.name

        try:

            result = model.transcribe(

                temp_path,

                language="ar",

                task="transcribe",

                temperature=0,

                beam_size=5,

                best_of=5,

                condition_on_previous_text=False,

                fp16=False,

                verbose=False
            )

            text = result.get(
                "text",
                ""
            )

            return text.strip()

        finally:

            if os.path.exists(
                temp_path
            ):

                os.remove(
                    temp_path
                )

    except Exception as e:

        st.error(
            f"❌ خطأ في Whisper: {e}"
        )

        return ""


# =========================================================
# استخراج الأرقام من النص
# =========================================================

def tokenize_text(text):

    if not text:

        return []

    text = normalize_numbers(
        text
    )

    text = normalize_arabic_letters(
        text
    )

    words = text.split()

    tokens = []

    for raw_word in words:

        word = clean_word(
            raw_word
        )

        if not word:
            continue

        if word in IGNORE_WORDS:
            continue

        # =================================================
        # 4 أرقام متصلة
        # =================================================

        if re.fullmatch(
            r"\d{4}",
            word
        ):

            tokens.append({

                "type":
                    "number4",

                "value":
                    word

            })

            continue

        # =================================================
        # أرقام متصلة بأي طول
        # =================================================

        if re.fullmatch(
            r"\d+",
            word
        ):

            for digit in word:

                tokens.append({

                    "type":
                        "digit",

                    "value":
                        digit

                })

            continue

        # =================================================
        # حرف
        # =================================================

        letter = word_to_letter(
            word
        )

        if letter:

            tokens.append({

                "type":
                    "letter",

                "value":
                    letter

            })

            continue

        # =================================================
        # رقم منطوق
        # =================================================

        digit = word_to_digit(
            word
        )

        if digit:

            tokens.append({

                "type":
                    "digit",

                "value":
                    digit

            })

            continue

        # =================================================
        # لو Whisper كتب 3 حروف ملتصقة
        # =================================================

        if re.fullmatch(
            r"[ا-ي]{3}",
            word
        ):

            for letter in word:

                tokens.append({

                    "type":
                        "letter",

                    "value":
                        letter

                })

            continue

        # =================================================
        # لو كلمة عبارة عن حرفين
        # =================================================

        if re.fullmatch(
            r"[ا-ي]{1,2}",
            word
        ):

            for letter in word:

                tokens.append({

                    "type":
                        "letter",

                    "value":
                        letter

                })

            continue

        tokens.append({

            "type":
                "other",

            "value":
                word

        })

    return tokens


# =========================================================
# البحث عن لوحة حول رقم
# =========================================================

def extract_around_number(
    tokens,
    number_index
):

    # =====================================================
    # نبحث للخلف عن 3 حروف
    # =====================================================

    letters = []

    j = number_index - 1

    while j >= 0 and len(letters) < 3:

        token = tokens[j]

        if token["type"] == "letter":

            letters.insert(
                0,
                token["value"]
            )

        elif token["type"] in (
            "other",
        ):

            # كلمة عادية تقطع التسلسل
            break

        j -= 1

    # =====================================================
    # الأرقام
    # =====================================================

    number = ""

    token = tokens[number_index]

    if token["type"] == "number4":

        number = token["value"]

    else:

        k = number_index

        while (
            k < len(tokens)
            and
            len(number) < 4
        ):

            current = tokens[k]

            if current["type"] == "digit":

                number += current["value"]

            elif current["type"] == "number4":

                number += current["value"]

            else:

                break

            k += 1

    if (
        len(letters) == 3
        and
        len(number) == 4
    ):

        return (
            "".join(letters)
            +
            number
        )

    return None


# =========================================================
# استخراج اللوحات
# =========================================================

def extract_all_plates(
    spoken_text
):

    if not spoken_text:

        return []

    results = []

    # =====================================================
    # أولاً: البحث المباشر
    #
    # رمص1077
    # =====================================================

    direct_pattern = re.compile(
        r"([ا-ي]{3})\s*(\d{4})"
    )

    normalized_text = (
        normalize_numbers(
            normalize_arabic_letters(
                spoken_text
            )
        )
    )

    for match in direct_pattern.finditer(
        normalized_text
    ):

        plate = (
            match.group(1)
            +
            match.group(2)
        )

        if plate not in results:

            results.append(
                plate
            )

    # =====================================================
    # Tokens
    # =====================================================

    tokens = tokenize_text(
        spoken_text
    )

    # =====================================================
    # البحث عن كل رقم 4 خانات
    # =====================================================

    for i, token in enumerate(
        tokens
    ):

        if token["type"] not in (
            "number4",
            "digit"
        ):

            continue

        plate = extract_around_number(
            tokens,
            i
        )

        if plate:

            if (
                len(plate) == 7
                and
                plate not in results
            ):

                results.append(
                    plate
                )

    # =====================================================
    # البحث عن نمط:
    #
    # 3 حروف + 4 أرقام
    #
    # حتى لو الأرقام مفصولة
    # =====================================================

    i = 0

    while i < len(tokens):

        if (
            i + 6 < len(tokens)
        ):

            first_seven = tokens[
                i:i + 7
            ]

            if all(
                x["type"] == "letter"
                for x in first_seven[:3]
            ):

                if all(
                    x["type"] == "digit"
                    for x in first_seven[3:]
                ):

                    letters = "".join(
                        x["value"]
                        for x in first_seven[:3]
                    )

                    numbers = "".join(
                        x["value"]
                        for x in first_seven[3:]
                    )

                    plate = (
                        letters
                        +
                        numbers
                    )

                    if (
                        len(plate) == 7
                        and
                        plate not in results
                    ):

                        results.append(
                            plate
                        )

        i += 1

    return results


# =========================================================
# مطابقة مع Excel
# =========================================================

def find_excel_match(
    spoken_plate,
    excel_plates
):

    letters, numbers = (
        get_plate_parts(
            spoken_plate
        )
    )

    if not letters:

        return None

    for plate in excel_plates:

        if (
            plate["letters"]
            ==
            letters
            and
            plate["numbers"]
            ==
            numbers
        ):

            return plate["original"]

    return None


# =========================================================
# عرض النتائج
# =========================================================

def display_results(
    spoken_text,
    plates
):

    matches = extract_all_plates(
        spoken_text
    )

    st.divider()

    st.header("📋 النتيجة")

    if not matches:

        st.error(
            "❌ لم يتم التعرف على أي لوحة."
        )

        return

    excel_plates = (
        prepare_excel_plates(
            plates
        )
    )

    st.success(
        f"✅ تم التعرف على {len(matches)} لوحة."
    )

    # =====================================================
    # اللوحات فقط
    # كل واحدة في سطر
    # =====================================================

    for plate in matches:

        excel_match = (
            find_excel_match(
                plate,
                excel_plates
            )
        )

        if excel_match:

            # =============================================
            # موجودة في Excel
            # أحمر
            # =============================================

            st.markdown(
                f"""
                <div style="
                    color:#ff3333;
                    font-size:34px;
                    font-weight:bold;
                    text-align:center;
                    padding:6px;
                    margin:2px;
                ">
                    {plate}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            # =============================================
            # غير موجودة
            # أبيض
            # =============================================

            st.markdown(
                f"""
                <div style="
                    color:white;
                    font-size:34px;
                    font-weight:bold;
                    text-align:center;
                    padding:6px;
                    margin:2px;
                ">
                    {plate}
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# رفع Excel
# =========================================================

st.divider()

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=[
        "xlsx",
        "xls"
    ]
)

plates = []

if uploaded_file is not None:

    try:

        df = pd.read_excel(
            uploaded_file
        )

        plate_column = None

        # =================================================
        # البحث عن عمود اللوحات
        # =================================================

        for column in df.columns:

            name = str(
                column
            ).strip()

            if name in [
                "اللوحه",
                "اللوحة",
                "لوحه",
                "لوحة",
                "رقم اللوحة",
                "رقم اللوحه",
            ]:

                plate_column = column

                break

        # =================================================
        # بحث أوسع
        # =================================================

        if plate_column is None:

            for column in df.columns:

                name = (
                    str(column)
                    .strip()
                    .replace(
                        " ",
                        ""
                    )
                )

                if "لوح" in name:

                    plate_column = column

                    break

        # =================================================
        # قراءة اللوحات
        # =================================================

        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود اللوحات في الملف."
            )

        else:

            raw_plates = (
                df[plate_column]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            plates = []

            for plate in raw_plates:

                letters, numbers = (
                    get_plate_parts(
                        plate
                    )
                )

                # =================================================
                # لازم 3 حروف + 4 أرقام
                # =================================================

                if (
                    letters
                    and
                    numbers
                ):

                    plates.append(
                        plate
                    )

            st.success(
                f"✅ تم تحميل {len(plates)} لوحة بنجاح."
            )

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء قراءة Excel: {e}"
        )


# =========================================================
# مصدر التسجيل
# =========================================================

st.divider()

st.header("🎙️ مصدر التسجيل")

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

            audio_bytes = (
                audio_recorded["bytes"]
            )

            with st.spinner(
                "🎙️ جاري تحليل التسجيل بـ Whisper واستخراج كل اللوحات..."
            ):

                spoken_text = (
                    transcribe_audio(
                        audio_bytes
                    )
                )

            if spoken_text:

                st.session_state[
                    "spoken_text"
                ] = spoken_text

                display_results(
                    spoken_text,
                    plates
                )

            else:

                st.error(
                    "❌ لم يتم التعرف على الكلام."
                )


# =========================================================
# رفع تسجيل من الجوال
# =========================================================

with tab2:

    uploaded_audio = st.file_uploader(

        "📁 اختاري التسجيل من الهاتف",

        type=[
            "wav",
            "mp3",
            "m4a",
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

            audio_bytes = (
                uploaded_audio.read()
            )

            with st.spinner(
                "🎙️ جاري تحليل التسجيل بـ Whisper واستخراج كل اللوحات..."
            ):

                spoken_text = (
                    transcribe_audio(
                        audio_bytes
                    )
                )

            if spoken_text:

                st.session_state[
                    "spoken_text"
                ] = spoken_text

                display_results(
                    spoken_text,
                    plates
                )

            else:

                st.error(
                    "❌ لم يتم التعرف على الكلام."
                )
