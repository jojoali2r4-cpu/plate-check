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
# تحويل الأرقام العربية
# =========================================================

def normalize_numbers(text):
    table = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789"
    )
    return str(text).translate(table)


# =========================================================
# إزالة التشكيل
# =========================================================

def remove_diacritics(text):
    return re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        str(text)
    )


# =========================================================
# تنظيف اللوحة
# =========================================================

def normalize_plate(text):

    text = normalize_numbers(text)
    text = remove_diacritics(text)

    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")

    text = re.sub(
        r"[\s\-_,.!؟،:؛]+",
        "",
        text
    )

    return text.strip()


# =========================================================
# قاموس الحروف
# =========================================================

LETTER_WORDS = {

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
    "راء": "ر",
    "را": "ر",
    "زاي": "ز",
    "زا": "ز",
    "سين": "س",
    "سي": "س",
    "شين": "ش",
    "شي": "ش",
    "صاد": "ص",
    "صا": "ص",
    "ضاد": "ض",
    "ضا": "ض",
    "طاء": "ط",
    "طا": "ط",
    "ظاء": "ظ",
    "ظا": "ظ",
    "عين": "ع",
    "عي": "ع",
    "غين": "غ",
    "غي": "غ",
    "فاء": "ف",
    "فا": "ف",
    "قاف": "ق",
    "قا": "ق",
    "كاف": "ك",
    "كا": "ك",
    "لام": "ل",
    "لا": "ل",
    "ميم": "م",
    "مي": "م",
    "نون": "ن",
    "نو": "ن",
    "هاء": "ه",
    "ها": "ه",
    "واو": "و",
    "وا": "و",
    "ياء": "ي",
    "يا": "ي",
}


# =========================================================
# قاموس الأرقام
# =========================================================

NUMBER_WORDS = {

    "صفر": "0",

    "واحد": "1",
    "واحدة": "1",

    "اثنين": "2",
    "اثنان": "2",
    "اتنين": "2",

    "ثلاثة": "3",
    "ثلاثه": "3",
    "ثلاث": "3",
    "تلاتة": "3",
    "تلاته": "3",

    "اربعة": "4",
    "أربعة": "4",
    "اربعه": "4",
    "أربعه": "4",

    "خمسة": "5",
    "خمسه": "5",
    "خمس": "5",

    "ستة": "6",
    "سته": "6",
    "ست": "6",

    "سبعة": "7",
    "سبعه": "7",
    "سبع": "7",

    "ثمانية": "8",
    "ثمانيه": "8",
    "تمانية": "8",
    "تمانيه": "8",

    "تسعة": "9",
    "تسعه": "9",
    "تسع": "9",
}


# =========================================================
# الكلمات التي لا تعتبر حروفًا
# =========================================================

IGNORE_WORDS = {
    "رقم",
    "الرقم",
    "لوحة",
    "اللوحة",
    "لوحه",
    "اللوحه",
    "حرف",
    "حروف",
    "موقع",
    "موجود",
    "في",
    "من",
    "على",
    "و",
    "هي",
    "هو",
}


# =========================================================
# تحويل كلمة إلى حرف
# =========================================================

def word_to_letter(word):

    word = remove_diacritics(word).strip()

    word = word.replace("أ", "ا")
    word = word.replace("إ", "ا")
    word = word.replace("آ", "ا")

    return LETTER_WORDS.get(word)


# =========================================================
# تحويل كلمة إلى رقم
# =========================================================

def word_to_digit(word):

    word = remove_diacritics(word).strip()

    word = word.replace("أ", "ا")
    word = word.replace("إ", "ا")
    word = word.replace("آ", "ا")

    return NUMBER_WORDS.get(word)


# =========================================================
# تحويل الصوت إلى WAV
# =========================================================

def convert_to_wav(audio_bytes):

    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes)
    )

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)

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

    except Exception as e:

        st.error(
            f"حدث خطأ أثناء تحويل الصوت إلى نص: {e}"
        )

        return ""


# =========================================================
# تقسيم الكلام
# =========================================================

def tokenize_text(text):

    text = normalize_numbers(text)
    text = remove_diacritics(text)

    return re.findall(
        r"\d+|[ء-ي]+",
        text
    )


# =========================================================
# استخراج 4 أرقام متتالية
# =========================================================

def extract_four_digits(tokens, start):

    digits = ""
    end = start

    while end < len(tokens) and len(digits) < 4:

        token = tokens[end]

        # رقم مكتوب مباشرة
        if re.fullmatch(r"\d+", token):

            digits += token

        else:

            digit = word_to_digit(token)

            if digit is None:
                break

            digits += digit

        end += 1

    # لازم بالضبط 4 أرقام
    if len(digits) == 4:

        return digits, end

    return None, start


# =========================================================
# استخراج 3 حروف قبل الأرقام
# =========================================================

def extract_three_letters(tokens, start):

    letters = []
    i = start

    while i < len(tokens) and len(letters) < 3:

        token = tokens[i]

        if token in IGNORE_WORDS:

            i += 1
            continue

        letter = word_to_letter(token)

        if letter is None:

            break

        letters.append(letter)

        i += 1

    if len(letters) == 3:

        return "".join(letters), i

    return None, start


# =========================================================
# استخراج اللوحات من الكلام
# =========================================================

def extract_spoken_plates(spoken_text):

    tokens = tokenize_text(
        spoken_text
    )

    plates_found = []

    i = 0

    while i < len(tokens):

        # نحاول إيجاد 3 حروف
        letters, after_letters = (
            extract_three_letters(
                tokens,
                i
            )
        )

        if letters is not None:

            # بعد الحروف مباشرة نبحث عن 4 أرقام
            digits, after_digits = (
                extract_four_digits(
                    tokens,
                    after_letters
                )
            )

            if digits is not None:

                plate = letters + digits

                # تأكيد نهائي:
                # 3 حروف + 4 أرقام فقط
                if re.fullmatch(
                    r"[ء-ي]{3}\d{4}",
                    plate
                ):

                    plates_found.append(
                        plate
                    )

                    i = after_digits

                    continue

        i += 1

    # إزالة التكرار
    unique = []

    for plate in plates_found:

        if plate not in unique:
            unique.append(plate)

    return unique


# =========================================================
# تطبيع كل لوحات Excel
# =========================================================

def prepare_excel_plates(plates):

    prepared = []

    for original in plates:

        normalized = normalize_plate(
            original
        )

        # اللوحة الصحيحة يجب أن تكون:
        # 3 حروف + 4 أرقام
        if re.fullmatch(
            r"[ء-ي]{3}\d{4}",
            normalized
        ):

            prepared.append(
                normalized
            )

    return prepared


# =========================================================
# البحث عن اللوحة نفسها فقط
# =========================================================

def plate_exists(
    spoken_plate,
    excel_plates
):

    spoken_plate = normalize_plate(
        spoken_plate
    )

    for excel_plate in excel_plates:

        if spoken_plate == excel_plate:

            return True

    return False


# =========================================================
# معالجة التسجيل
# =========================================================

def process_audio(
    audio_bytes,
    excel_plates
):

    if not excel_plates:

        st.warning(
            "⚠️ ارفعي ملف Excel أولاً."
        )

        return

    with st.spinner(
        "🎙️ جاري التعرف على التسجيل..."
    ):

        spoken_text = audio_to_text(
            audio_bytes
        )

    if not spoken_text:

        st.error(
            "❌ لم أستطع فهم التسجيل."
        )

        return

    spoken_plates = (
        extract_spoken_plates(
            spoken_text
        )
    )

    results = []

    for plate in spoken_plates:

        exists = plate_exists(
            plate,
            excel_plates
        )

        results.append(
            {
                "plate": plate,
                "exists": exists
            }
        )

    st.session_state.results = results


# =========================================================
# رفع Excel
# =========================================================

st.divider()

st.header("📁 ملف اللوحات")

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"],
    key="excel_upload"
)

excel_plates = []

if uploaded_file is not None:

    try:

        df = pd.read_excel(
            uploaded_file
        )

        # البحث عن اسم العمود
        plate_column = None

        for column in df.columns:

            column_name = str(
                column
            ).strip()

            if column_name in [
                "اللوحه",
                "اللوحة",
                "لوحه",
                "لوحة",
                "plate",
                "Plate"
            ]:

                plate_column = column
                break

        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود «اللوحه» أو «اللوحة» في ملف Excel."
            )

        else:

            raw_plates = (
                df[plate_column]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            excel_plates = prepare_excel_plates(
                raw_plates
            )

            st.success(
                f"✅ تم تحميل {len(raw_plates)} لوحة بنجاح."
            )

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء قراءة ملف Excel: {e}"
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
# تسجيل مباشر
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

        audio_bytes = (
            audio_recorded["bytes"]
        )

        process_audio(
            audio_bytes,
            excel_plates
        )


# =========================================================
# رفع أي ملف صوتي من الهاتف
# =========================================================

with tab2:

    st.write(
        "📁 اختاري أي ملف صوتي من ملفات الهاتف:"
    )

    uploaded_audio = st.file_uploader(

        "🎵 اختيار ملف صوتي",

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

        audio_bytes = (
            uploaded_audio.getvalue()
        )

        process_audio(
            audio_bytes,
            excel_plates
        )


# =========================================================
# النتيجة
# =========================================================

st.divider()

st.header("📋 النتيجة")

if "results" not in st.session_state:

    st.session_state.results = []


if st.session_state.results:

    st.success(
        f"✅ تم التعرف على {len(st.session_state.results)} لوحة."
    )

    for result in st.session_state.results:

        plate = result["plate"]
        exists = result["exists"]

        if exists:

            st.markdown(
                f"""
                <div style="
                    background:#4a1820;
                    border:2px solid #ff4b4b;
                    border-radius:14px;
                    padding:18px;
                    margin:12px 0;
                    text-align:center;
                ">

                    <div style="
                        color:#ff4b4b;
                        font-size:32px;
                        font-weight:bold;
                    ">
                        🚗 {plate}
                    </div>

                    <div style="
                        color:#ff6b6b;
                        font-size:20px;
                        margin-top:8px;
                    ">
                        🔴 موجودة في الملف
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div style="
                    background:#202126;
                    border:1px solid #555;
                    border-radius:14px;
                    padding:18px;
                    margin:12px 0;
                    text-align:center;
                ">

                    <div style="
                        color:white;
                        font-size:32px;
                        font-weight:bold;
                    ">
                        🚗 {plate}
                    </div>

                    <div style="
                        color:#aaaaaa;
                        font-size:20px;
                        margin-top:8px;
                    ">
                        ⚪ غير موجودة في الملف
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

else:

    st.info(
        "🎙️ سجلي أو ارفعي تسجيلًا للبحث عن اللوحات."
    )
