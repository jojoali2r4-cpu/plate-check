import streamlit as st
import pandas as pd
import speech_recognition as sr
import re
import io
from pydub import AudioSegment
from streamlit_mic_recorder import mic_recorder
from concurrent.futures import ThreadPoolExecutor, as_completed


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
# تطبيع الأرقام
# =========================================================

def normalize_numbers(text):

    if not text:
        return ""

    arabic_numbers = "٠١٢٣٤٥٦٧٨٩"
    english_numbers = "0123456789"

    table = str.maketrans(
        arabic_numbers,
        english_numbers
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

    text = str(text)

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

    text = normalize_numbers(text)
    text = normalize_arabic_letters(text)

    text = text.lower()

    text = re.sub(
        r"[\s\-_,.!؟،:؛/\\]+",
        "",
        text
    )

    return text


# =========================================================
# أسماء الحروف العربية
# =========================================================

LETTER_NAMES = {

    "الف": "ا",
    "الفا": "ا",

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
    "دا": "د",

    "ذال": "ذ",
    "ذا": "ذ",

    "راء": "ر",
    "را": "ر",

    "زاي": "ز",
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
# أسماء الأرقام العربية
# =========================================================

NUMBER_WORDS = {

    "صفر": "0",

    "واحد": "1",
    "واحدة": "1",

    "اثنان": "2",
    "اثنين": "2",
    "اثنتين": "2",
    "اتنين": "2",
    "اتنان": "2",

    "ثلاثة": "3",
    "ثلاث": "3",

    "اربعة": "4",
    "أربعة": "4",
    "اربعه": "4",
    "أربعه": "4",

    "خمسة": "5",
    "خمسه": "5",

    "ستة": "6",
    "سته": "6",
    "ست": "6",

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
# تحويل أسماء الحروف إلى حروف
# =========================================================

def convert_spoken_letters(text):

    if not text:
        return ""

    text = normalize_numbers(text)
    text = normalize_arabic_letters(text)

    text = re.sub(
        r"[،,؛;.!؟?_\-]+",
        " ",
        text
    )

    words = text.split()

    result = []

    for word in words:

        cleaned = clean_text(word)

        if cleaned in LETTER_NAMES:

            result.append(
                LETTER_NAMES[cleaned]
            )

        else:

            # الحروف المكتوبة مباشرة
            chars = re.findall(
                r"[^\W\d_]",
                word,
                flags=re.UNICODE
            )

            if len(chars) > 0:
                result.extend(chars)

    return "".join(result)


# =========================================================
# تحويل كلمات الأرقام إلى أرقام
# =========================================================

def convert_spoken_numbers(text):

    if not text:
        return ""

    text = normalize_numbers(text)

    words = text.split()

    result = []

    for word in words:

        cleaned = clean_text(word)

        if cleaned in NUMBER_WORDS:

            result.append(
                NUMBER_WORDS[cleaned]
            )

    return "".join(result)


# =========================================================
# تجهيز اللوحة من Excel
# =========================================================

def normalize_plate(plate):

    if plate is None:
        return ""

    plate = normalize_numbers(str(plate))
    plate = normalize_arabic_letters(plate)

    plate = re.sub(
        r"[\s\-_,.!؟،:؛/\\]+",
        "",
        plate
    )

    return plate.strip()


# =========================================================
# استخراج 3 حروف + 4 أرقام
# =========================================================

def get_plate_parts(plate):

    normalized = normalize_plate(plate)

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
        and len(numbers) == 4
    ):
        return letters, numbers

    return None, None


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
# تحويل مقطع واحد إلى نص
# =========================================================

def recognize_chunk(chunk):

    recognizer = sr.Recognizer()

    wav_buffer = io.BytesIO()

    chunk.export(
        wav_buffer,
        format="wav"
    )

    wav_buffer.seek(0)

    try:

        with sr.AudioFile(
            wav_buffer
        ) as source:

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

    except Exception:

        return ""


# =========================================================
# تحويل التسجيل الطويل إلى نص
# =========================================================

def audio_to_text_long(audio_bytes):

    try:

        audio = AudioSegment.from_file(
            io.BytesIO(audio_bytes)
        )

        # التسجيل إلى أجزاء 20 ثانية
        chunk_length = 20 * 1000

        # تداخل 4 ثواني حتى لا تضيع لوحة
        # عند نهاية وبداية مقطعين
        overlap = 4 * 1000

        chunks = []

        start = 0

        while start < len(audio):

            end = min(
                start + chunk_length,
                len(audio)
            )

            chunk = audio[
                max(0, start - overlap):end
            ]

            chunks.append(chunk)

            start += (
                chunk_length - overlap
            )

        results = [""] * len(chunks)

        # تشغيل عدة مقاطع في نفس الوقت
        with ThreadPoolExecutor(
            max_workers=4
        ) as executor:

            futures = {
                executor.submit(
                    recognize_chunk,
                    chunk
                ): i
                for i, chunk in enumerate(chunks)
            }

            for future in as_completed(
                futures
            ):

                index = futures[future]

                try:

                    results[index] = (
                        future.result()
                    )

                except Exception:

                    results[index] = ""

        final_text = " ".join(
            r for r in results if r
        )

        return final_text

    except Exception as e:

        st.error(
            f"حدث خطأ أثناء معالجة التسجيل: {e}"
        )

        return ""


# =========================================================
# استخراج مجموعات الأرقام
# =========================================================

def extract_number_groups(text):

    if not text:
        return []

    text = normalize_numbers(text)

    groups = []

    # -----------------------------------------------------
    # أرقام متصلة
    # -----------------------------------------------------

    for match in re.finditer(
        r"\d{4}",
        text
    ):

        groups.append(
            match.group()
        )

    # -----------------------------------------------------
    # الأرقام الموجودة ككلمات
    # -----------------------------------------------------

    word_number_sequences = []

    words = text.split()

    current = ""

    for word in words:

        cleaned = clean_text(word)

        if cleaned in NUMBER_WORDS:

            current += NUMBER_WORDS[cleaned]

            if len(current) == 4:

                word_number_sequences.append(
                    current
                )

                current = ""

            elif len(current) > 4:

                current = ""

        else:

            if current:
                current = ""

    groups.extend(
        word_number_sequences
    )

    # -----------------------------------------------------
    # أرقام مفصولة
    # مثال:
    # 24 34
    # -----------------------------------------------------

    tokens = re.findall(
        r"\d+",
        text
    )

    for i in range(
        len(tokens)
    ):

        # رقم 4 خانات
        if len(tokens[i]) == 4:

            groups.append(
                tokens[i]
            )

        # 24 + 34
        if (
            len(tokens[i]) == 2
            and
            i + 1 < len(tokens)
            and
            len(tokens[i + 1]) == 2
        ):

            groups.append(
                tokens[i]
                + tokens[i + 1]
            )

        # 2 + 4 + 3 + 4
        if (
            len(tokens[i]) == 1
            and
            i + 3 < len(tokens)
            and
            len(tokens[i + 1]) == 1
            and
            len(tokens[i + 2]) == 1
            and
            len(tokens[i + 3]) == 1
        ):

            groups.append(
                tokens[i]
                + tokens[i + 1]
                + tokens[i + 2]
                + tokens[i + 3]
            )

    # إزالة التكرار
    groups = list(
        dict.fromkeys(groups)
    )

    return groups


# =========================================================
# استخراج اللوحات من الكلام
# =========================================================

def find_spoken_plates(
    spoken_text,
    plates
):

    if not spoken_text:
        return []

    if not plates:
        return []

    spoken_text = normalize_numbers(
        spoken_text
    )

    spoken_text = normalize_arabic_letters(
        spoken_text
    )

    # -----------------------------------------------------
    # تجهيز لوحات Excel
    # -----------------------------------------------------

    excel_plates = []

    for original in plates:

        letters, numbers = get_plate_parts(
            original
        )

        if (
            letters
            and numbers
        ):

            excel_plates.append(
                {
                    "original": str(
                        original
                    ).strip(),

                    "letters": letters,

                    "numbers": numbers,

                    "normalized": normalize_plate(
                        original
                    )
                }
            )

    # -----------------------------------------------------
    # الأرقام الموجودة في الكلام
    # -----------------------------------------------------

    number_groups = extract_number_groups(
        spoken_text
    )

    results = []

    # -----------------------------------------------------
    # البحث عن كل رقم
    # -----------------------------------------------------

    for number in number_groups:

        # كل لوحات Excel التي تحمل نفس الرقم
        possible_excel = [
            p
            for p in excel_plates
            if p["numbers"] == number
        ]

        # -------------------------------------------------
        # تحديد أماكن الرقم في النص
        # -------------------------------------------------

        positions = [
            m.start()
            for m in re.finditer(
                re.escape(number),
                spoken_text
            )
        ]

        for position in positions:

            # الكلام قبل الرقم
            before_start = max(
                0,
                position - 100
            )

            before = spoken_text[
                before_start:position
            ]

            # -------------------------------------------------
            # تحويل أسماء الحروف
            # -------------------------------------------------

            spoken_letters = (
                convert_spoken_letters(
                    before
                )
            )

            # -------------------------------------------------
            # إذا Google كتب الحروف مباشرة
            # -------------------------------------------------

            direct_letters = "".join(
                re.findall(
                    r"[^\W\d_]",
                    before,
                    flags=re.UNICODE
                )
            )

            # -------------------------------------------------
            # آخر 3 حروف
            # -------------------------------------------------

            letter_candidates = []

            if len(spoken_letters) >= 3:

                letter_candidates.append(
                    spoken_letters[-3:]
                )

            if len(direct_letters) >= 3:

                letter_candidates.append(
                    direct_letters[-3:]
                )

            # إزالة التكرار
            letter_candidates = list(
                dict.fromkeys(
                    letter_candidates
                )
            )

            # -------------------------------------------------
            # أولًا: مطابقة مباشرة مع Excel
            # -------------------------------------------------

            found_excel = False

            for candidate in possible_excel:

                for letters in letter_candidates:

                    if (
                        letters
                        == candidate["letters"]
                    ):

                        if (
                            candidate["original"]
                            not in results
                        ):

                            results.append(
                                candidate["original"]
                            )

                        found_excel = True

                        break

                if found_excel:
                    break

            if found_excel:
                continue

            # -------------------------------------------------
            # لو اللوحة غير موجودة في Excel
            # نحتاج استخراجها من الكلام نفسه
            # -------------------------------------------------

            # نبحث عن صيغة:
            # 3 حروف + الرقم
            # -------------------------------------------------

            # نأخذ آخر 3 حروف معروفة
            if letter_candidates:

                letters = (
                    letter_candidates[-1]
                )

                if len(letters) == 3:

                    candidate_plate = (
                        letters
                        + number
                    )

                    # لا نضيف إلا لوحة صحيحة
                    if (
                        len(candidate_plate) == 7
                    ):

                        if (
                            candidate_plate
                            not in results
                        ):

                            results.append(
                                candidate_plate
                            )

    return results


# =========================================================
# البحث في Excel بالضبط
# =========================================================

def is_plate_in_excel(
    plate,
    plates
):

    normalized = normalize_plate(
        plate
    )

    for excel_plate in plates:

        if (
            normalize_plate(
                excel_plate
            )
            == normalized
        ):

            return True

    return False


# =========================================================
# عرض النتائج
# =========================================================

def display_results(
    spoken_text,
    plates
):

    matches = find_spoken_plates(
        spoken_text,
        plates
    )

    st.divider()

    st.header("📋 النتيجة")

    if not matches:

        st.error(
            "❌ لم يتم التعرف على أي لوحة."
        )

        return

    st.success(
        f"✅ تم التعرف على {len(matches)} لوحة."
    )

    # -----------------------------------------------------
    # عرض كل لوحة في سطر
    # -----------------------------------------------------

    for plate in matches:

        exists = is_plate_in_excel(
            plate,
            plates
        )

        if exists:

            st.markdown(
                f"""
                <div style="
                    color:#ff3333;
                    font-size:32px;
                    font-weight:bold;
                    padding:10px 5px;
                    direction:rtl;
                    text-align:right;
                ">
                    🚗 {plate}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div style="
                    color:white;
                    font-size:32px;
                    font-weight:bold;
                    padding:10px 5px;
                    direction:rtl;
                    text-align:right;
                ">
                    🚗 {plate}
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# رفع ملف Excel
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

        # -------------------------------------------------
        # البحث عن عمود اللوحات
        # -------------------------------------------------

        for column in df.columns:

            column_name = str(
                column
            ).strip()

            if column_name in [
                "اللوحه",
                "اللوحة",
                "لوحه",
                "لوحة"
            ]:

                plate_column = column
                break

        # -------------------------------------------------
        # بحث أوسع
        # -------------------------------------------------

        if plate_column is None:

            for column in df.columns:

                column_name = (
                    str(column)
                    .strip()
                    .replace(
                        " ",
                        ""
                    )
                )

                if "لوح" in column_name:

                    plate_column = column
                    break

        # -------------------------------------------------
        # إذا لم يوجد العمود
        # -------------------------------------------------

        if plate_column is None:

            st.error(
                "❌ لم يتم العثور على عمود اللوحات في ملف Excel."
            )

        else:

            plates = (
                df[plate_column]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            # -------------------------------------------------
            # الاحتفاظ فقط باللوحات التي:
            # 3 حروف + 4 أرقام
            # -------------------------------------------------

            valid_plates = []

            for plate in plates:

                letters, numbers = (
                    get_plate_parts(
                        plate
                    )
                )

                if (
                    letters
                    and numbers
                    and len(letters) == 3
                    and len(numbers) == 4
                ):

                    valid_plates.append(
                        plate
                    )

            plates = valid_plates

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
                "⚠️ ارفعي ملف Excel أولًا."
            )

        else:

            audio_bytes = (
                audio_recorded["bytes"]
            )

            with st.spinner(
                "🎙️ جاري تحليل التسجيل واستخراج جميع اللوحات..."
            ):

                spoken_text = (
                    audio_to_text_long(
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
                    "❌ لم يتم التعرف على الكلام في التسجيل."
                )


# =========================================================
# رفع تسجيل من الجوال
# =========================================================

with tab2:

    uploaded_audio = st.file_uploader(

        "📁 اختاري أي ملف صوتي من ملفات الهاتف",

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
                "⚠️ ارفعي ملف Excel أولًا."
            )

        else:

            audio_bytes = (
                uploaded_audio.read()
            )

            with st.spinner(
                "🎙️ جاري تحليل التسجيل واستخراج جميع اللوحات..."
            ):

                spoken_text = (
                    audio_to_text_long(
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
                    "❌ لم يتم التعرف على الكلام في التسجيل."
                )
