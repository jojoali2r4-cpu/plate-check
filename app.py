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

    table = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789"
    )

    return str(text).translate(table)


# =========================================================
# تطبيع الحروف
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
        "ئ": "ي"
    }

    text = str(text)

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# =========================================================
# تنظيف النص
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = normalize_numbers(text)
    text = normalize_arabic_letters(text)

    text = text.lower()

    text = re.sub(
        r"[\s\-_,.!؟،:؛/\\]+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# أسماء الحروف
# =========================================================

LETTER_NAMES = {

    "الف": "ا",
    "الفا": "ا",
    "همزه": "ا",

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
# الحروف المكتوبة مباشرة
# =========================================================

DIRECT_LETTERS = set(
    "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
)


# =========================================================
# أسماء الأرقام
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
    "اثنينه": "2",

    "ثلاثة": "3",
    "ثلاث": "3",
    "تلاتة": "3",
    "تلات": "3",

    "اربعة": "4",
    "أربعة": "4",
    "اربعه": "4",
    "أربعه": "4",
    "اربعه": "4",

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
    "ثمان": "8",

    "تسعة": "9",
    "تسعه": "9",
}


# =========================================================
# تحويل كلمة حرف إلى حرف
# =========================================================

def letter_from_word(word):

    word = clean_text(word)

    return LETTER_NAMES.get(word)


# =========================================================
# استخراج الحروف من جزء من الكلام
# =========================================================

def extract_letters_from_text(text):

    if not text:
        return ""

    text = normalize_arabic_letters(text)

    words = text.split()

    result = []

    for word in words:

        word_clean = clean_text(word)

        # اسم حرف
        if word_clean in LETTER_NAMES:

            result.append(
                LETTER_NAMES[word_clean]
            )

        # حرف واحد مكتوب مباشرة
        elif (
            len(word_clean) == 1
            and word_clean in DIRECT_LETTERS
        ):

            result.append(word_clean)

    return "".join(result)


# =========================================================
# استخراج الأرقام من الكلام
# =========================================================

def extract_numbers_from_text(text):

    if not text:
        return ""

    text = normalize_numbers(text)

    words = text.split()

    result = []

    for word in words:

        cleaned = clean_text(word)

        # رقم مكتوب كرقم
        if re.fullmatch(r"\d+", cleaned):

            result.append(cleaned)

        # رقم مكتوب بالكلمة
        elif cleaned in NUMBER_WORDS:

            result.append(
                NUMBER_WORDS[cleaned]
            )

    return "".join(result)


# =========================================================
# تجهيز لوحة Excel
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
# تجهيز Excel
# =========================================================

def prepare_excel_plates(plates):

    result = []

    for original in plates:

        letters, numbers = get_plate_parts(
            original
        )

        if letters and numbers:

            result.append({
                "original": str(original).strip(),
                "letters": letters,
                "numbers": numbers,
                "normalized": normalize_plate(original)
            })

    return result


# =========================================================
# تحويل التسجيل إلى AudioSegment
# =========================================================

def load_audio(audio_bytes):

    audio = AudioSegment.from_file(
        io.BytesIO(audio_bytes)
    )

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    return audio


# =========================================================
# تحويل مقطع واحد إلى نص
# =========================================================

def recognize_chunk(chunk):

    recognizer = sr.Recognizer()

    # تقليل الضوضاء
    chunk = chunk.set_channels(1)
    chunk = chunk.set_frame_rate(16000)

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

        # Google Speech Recognition مجاني
        text = recognizer.recognize_google(
            audio_data,
            language="ar-EG"
        )

        return text

    except sr.UnknownValueError:

        return ""

    except sr.RequestError:

        return ""

    except Exception:

        return ""


# =========================================================
# التسجيل الطويل
# =========================================================

def audio_to_text_long(audio_bytes):

    try:

        audio = load_audio(audio_bytes)

        # أقصى مدة 3 دقائق
        max_length = 3 * 60 * 1000

        if len(audio) > max_length:

            audio = audio[:max_length]

        # -------------------------------------------------
        # مقاطع 10 ثواني
        # -------------------------------------------------

        chunk_length = 10 * 1000

        # تداخل ثانيتين
        overlap = 2 * 1000

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

        # -------------------------------------------------
        # معالجة عدة مقاطع
        # -------------------------------------------------

        with ThreadPoolExecutor(
            max_workers=3
        ) as executor:

            futures = {
                executor.submit(
                    recognize_chunk,
                    chunk
                ): index

                for index, chunk
                in enumerate(chunks)
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

        # المحافظة على ترتيب التسجيل
        final_text = " ".join(
            text
            for text in results
            if text
        )

        return final_text

    except Exception as e:

        st.error(
            f"❌ حدث خطأ أثناء معالجة التسجيل: {e}"
        )

        return ""


# =========================================================
# استخراج أرقام من النص
# =========================================================

def extract_number_candidates(text):

    if not text:
        return []

    text = normalize_numbers(text)
    text = normalize_arabic_letters(text)

    candidates = []

    # -----------------------------------------------------
    # أرقام متصلة
    # -----------------------------------------------------

    for match in re.finditer(
        r"\d{4}",
        text
    ):

        candidates.append(
            match.group()
        )

    # -----------------------------------------------------
    # تحويل كلمات الأرقام إلى أرقام
    # -----------------------------------------------------

    words = text.split()

    converted = []

    for word in words:

        cleaned = clean_text(word)

        if cleaned in NUMBER_WORDS:

            converted.append(
                NUMBER_WORDS[cleaned]
            )

        elif re.fullmatch(
            r"\d+",
            cleaned
        ):

            converted.append(
                cleaned
            )

        else:

            converted.append("")

    # -----------------------------------------------------
    # البحث عن 4 أرقام متتابعة
    # -----------------------------------------------------

    for i in range(
        len(converted)
    ):

        current = ""

        for j in range(
            i,
            min(
                i + 6,
                len(converted)
            )
        ):

            if not converted[j]:
                break

            current += converted[j]

            if len(current) == 4:

                candidates.append(
                    current
                )

                break

            if len(current) > 4:

                break

    # -----------------------------------------------------
    # إزالة التكرار
    # -----------------------------------------------------

    return list(
        dict.fromkeys(candidates)
    )


# =========================================================
# استخراج اللوحات
# =========================================================

def find_spoken_plates(
    spoken_text,
    excel_plates
):

    if not spoken_text:
        return []

    if not excel_plates:
        return []

    text = normalize_numbers(
        spoken_text
    )

    text = normalize_arabic_letters(
        text
    )

    words = text.split()

    found = []

    # =====================================================
    # الطريقة الأساسية:
    # نمشي على الكلام كله ونبحث عن
    # 3 حروف + 4 أرقام
    # =====================================================

    for i in range(len(words)):

        # نأخذ نافذة حول كل مكان
        window_start = max(
            0,
            i - 8
        )

        window_end = min(
            len(words),
            i + 9
        )

        window_words = words[
            window_start:window_end
        ]

        window_text = " ".join(
            window_words
        )

        # الأرقام في النافذة
        number_candidates = (
            extract_number_candidates(
                window_text
            )
        )

        if not number_candidates:
            continue

        # الحروف في النافذة
        letter_sequence = (
            extract_letters_from_text(
                window_text
            )
        )

        if len(letter_sequence) < 3:
            continue

        # آخر 3 حروف
        possible_letters = (
            letter_sequence[-3:]
        )

        # =================================================
        # مقارنة مع Excel
        # =================================================

        for number in number_candidates:

            for plate in excel_plates:

                if plate["numbers"] != number:
                    continue

                if (
                    plate["letters"]
                    == possible_letters
                ):

                    original = plate[
                        "original"
                    ]

                    if original not in found:

                        found.append(
                            original
                        )

    # =====================================================
    # طريقة ثانية:
    # نبحث مباشرة عن كل لوحة Excel في الكلام
    # بعد تحويل أسماء الحروف والأرقام
    # =====================================================

    for plate in excel_plates:

        letters = plate["letters"]
        numbers = plate["numbers"]

        # لو الأرقام موجودة
        if numbers not in text:
            continue

        # نبحث عن أسماء الحروف المرتبطة باللوحة
        letter_names = []

        for letter in letters:

            names = [
                key
                for key, value
                in LETTER_NAMES.items()
                if value == letter
            ]

            letter_names.extend(names)

        # نتحقق من وجود تسلسل من 3 حروف
        for j in range(
            len(words)
        ):

            section = " ".join(
                words[
                    j:min(
                        j + 12,
                        len(words)
                    )
                ]
            )

            extracted = (
                extract_letters_from_text(
                    section
                )
            )

            if (
                len(extracted) >= 3
                and
                extracted[-3:] == letters
            ):

                if plate["original"] not in found:

                    found.append(
                        plate["original"]
                    )

                break

    return found


# =========================================================
# مطابقة اللوحات الموجودة في Excel
# =========================================================

def plate_exists_in_excel(
    plate,
    excel_plates
):

    normalized = normalize_plate(
        plate
    )

    for item in excel_plates:

        if (
            item["normalized"]
            == normalized
        ):

            return True

    return False


# =========================================================
# استخراج كل اللوحات التي تم نطقها
# =========================================================

def display_results(
    spoken_text,
    plates
):

    excel_plates = prepare_excel_plates(
        plates
    )

    matches = find_spoken_plates(
        spoken_text,
        excel_plates
    )

    st.divider()

    st.header("📋 النتيجة")

    if not matches:

        st.error(
            "❌ لم يتم العثور على أي لوحة."
        )

        # مفيد لمعرفة ماذا فهم
