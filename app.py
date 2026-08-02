import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="فحص اللوحات الذكي التلقائي", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 20px !important; font-weight: bold; text-align: right; padding: 15px; border-radius: 12px; margin-top: 15px; background-color: #f8f9fa; border: 2px solid #ccc; color: #333; }
    .mic-btn { font-size: 18px; padding: 14px 28px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; margin: 5px; width: 48%; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    .clear-btn { background-color: #6c757d; color: white; }
    .plate-item { background: #e2f0d9; padding: 12px; margin: 6px 0; border-radius: 6px; font-weight: bold; color: #274e13; font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام فحص اللوحات التلقائي (بالصوت فقط)")
st.markdown("---")

def parse_plate(text):
    if not text:
        return "", ""

    text = str(text).strip()

    # توحيد الأرقام العربية
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(arabic_digits, english_digits))

    # إزالة المسافات والرموز
    text = re.sub(r"[^\w\u0600-\u06FF]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    digits = "".join(re.findall(r"[0-9]", text))
    letters = "".join(re.findall(r"[\u0600-\u06FF]", text))
    return letters, digits


uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)

    raw_plates = df[column_name].dropna().tolist()
    plate_database = []

    for plate in raw_plates:
        letters, digits = parse_plate(plate)
        if len(letters) == 3 and len(digits) == 4:
            plate_database.append({
                "original": str(plate).strip(),
                "letters": letters,
                "digits": digits
            })

    st.success(f"تم تحميل {len(plate_database)} لوحة صالحة (3 حروف و4 أرقام) بنجاح!")
    st.markdown("---")

    st.subheader("🎙️ الفحص الصوتي التلقائي:")
    st.write("اضغطي على زر التشغيل وانطقي اللوحة مباشرة:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = """
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <div>
            <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع</button>
            <button class="mic-btn clear-btn" onclick="clearText()" style="width: 48%;">🗑️ مسح</button>
        </div>

        <div id="status" style="margin-top: 10px; color: #666; font-size: 14px;">الميكروفون متوقف</div>

        <div style="margin-top: 15px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <div style="font-size: 14px; color: #555;">النص المنطوق تلقائياً:</div>
            <div id="liveText" style="font-size: 28px; font-weight: bold; color: #007bff; min-height: 40px;">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;">
            <div style="font-weight: bold; margin-bottom: 8px; color: #111;">اللوحة المطابقة تماماً بالملف:</div>
            <div id="platesList"></div>
        </div>
    </div>

    <script>
        const plateDB = __DB__;

        let recognizing = false;
        let recognition = null;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        // ====== أدوات التطبيع والتحويل ======
        const digitWords = {
            "صفر": "0",
            "واحد": "1",
            "احد": "1",
            "إحد": "1",
            "اثنين": "2",
            "اثنان": "2",
            "اتنين": "2",
            "ثنين": "2",
            "ثلاثة": "3",
            "تلاتة": "3",
            "ثلاث": "3",
            "تلات": "3",
            "اربعة": "4",
            "أربعة": "4",
            "اربعه": "4",
            "أربعه": "4",
            "أربع": "4",
            "اربع": "4",
            "خمسة": "5",
            "خمسه": "5",
            "ستة": "6",
            "سته": "6",
            "سبعة": "7",
            "سبعه": "7",
            "ثمانية": "8",
            "تمانية": "8",
            "ثمانيه": "8",
            "تمنية": "8",
            "تمنيه": "8",
            "تسعة": "9",
            "تسعه": "9"
        };

        // أسماء الحروف المنطوقة -> الحرف نفسه
        const letterWords = {
            "ألف": "ا",
            "الف": "ا",
            "باء": "ب",
            "با": "ب",
            "بيه": "ب",
            "ب": "ب",

            "تاء": "ت",
            "تا": "ت",
            "تيه": "ت",
            "ت": "ت",

            "ثاء": "ث",
            "ثا": "ث",
            "ث": "ث",

            "جيم": "ج",
            "ج": "ج",

            "حاء": "ح",
            "حا": "ح",
            "ح": "ح",

            "خاء": "خ",
            "خا": "خ",
            "خ": "خ",

            "دال": "د",
            "د": "د",

            "ذال": "ذ",
            "ذ": "ذ",

            "راء": "ر",
            "راءً": "ر",
            "را": "ر",
            "ر": "ر",

            "زاي": "ز",
            "ز": "ز",

            "سين": "س",
            "س": "س",

            "شين": "ش",
            "ش": "ش",

            "صاد": "ص",
            "ص": "ص",

            "ضاد": "ض",
            "ض": "ض",

            "طاء": "ط",
            "طا": "ط",
            "ط": "ط",

            "ظاء": "ظ",
            "ظا": "ظ",
            "ظ": "ظ",

            "عين": "ع",
            "ع": "ع",

            "غين": "غ",
            "غ": "غ",

            "فاء": "ف",
            "فا": "ف",
            "ف": "ف",

            "قاف": "ق",
            "قا": "ق",
            "ق": "ق",

            "كاف": "ك",
            "كا": "ك",
            "ك": "ك",

            "لام": "ل",
            "لا": "ل",
            "ل": "ل",

            "ميم": "م",
            "ما": "م",
            "م": "م",

            "نون": "ن",
            "ن": "ن",

            "هاء": "ه",
            "ها": "ه",
            "ه": "ه",

            "واو": "و",
            "و": "و",

            "ياء": "ي",
            "يا": "ي",
            "ييه": "ي",
            "ي": "ي"
        };

        function normalizeArabic(text) {
            if (!text) return "";
            return text
                .toString()
                .trim()
                .replace(/[أإآا]/g, "ا")
                .replace(/ى/g, "ي")
                .replace(/ة/g, "ه")
                .replace(/ؤ/g, "و")
                .replace(/ئ/g, "ي")
                .replace(/[ًٌٍَُِّْـ]/g, "")
                .replace(/[^\w\u0600-\u06FF\s]/g, " ")
                .replace(/\s+/g, " ")
                .trim();
        }

        function convertWordToDigit(word) {
            const w = normalizeArabic(word);
            return digitWords[w] ?? null;
        }

        function convertWordToLetter(word) {
            const w = normalizeArabic(word);
            return letterWords[w] ?? null;
        }

        // يلتقط 3 حروف و 4 أرقام بالترتيب من الكلام
        function extractPlateParts(text) {
            let t = normalizeArabic(text);
            if (!t) return { letters: "", digits: "", raw: "" };

            // لو ظهر رقم مباشر مثل 4057 نحتفظ به كما هو
            const directDigits = (t.match(/[0-9]/g) || []).join("");

            // تقسيم الكلام لكلمات
            const tokens = t.split(/\s+/).filter(Boolean);

            let letters = "";
            let digits = "";

            for (let token of tokens) {
                token = normalizeArabic(token);
                if (!token) continue;

                // لو التوكن كله أرقام
                if (/^[0-9]+$/.test(token)) {
                    digits += token;
                    continue;
                }

                // لو التوكن اسم رقم
                const d = convertWordToDigit(token);
                if (d !== null) {
                    digits += d;
                    continue;
                }

                // لو التوكن حرف واحد مباشر
                if (/^[\u0600-\u06FF]$/.test(token)) {
                    const l = convertWordToLetter(token);
                    if (l) letters += l;
                    continue;
                }

                // لو التوكن اسم حرف
                const l2 = convertWordToLetter(token);
                if (l2) {
                    letters += l2;
                    continue;
                }

                // حالات مثل: باءباءياء أو باءبباء
                // نمر على كل مقطع ونلتقط الحروف العربية المفردة فقط
                const arabicChars = token.match(/[\u0600-\u06FF]/g) || [];
                for (const ch of arabicChars) {
                    const mapped = convertWordToLetter(ch);
                    if (mapped) letters += mapped;
                }
            }

            // لو ما قدرنا نلتقط 4 أرقام من الكلمات، نستخدم الأرقام المكتوبة مباشرة
            if (digits.length < 4 && directDigits.length > digits.length) {
                digits = directDigits;
            }

            // فقط أول 3 حروف وأول 4 أرقام
            letters = letters.replace(/[^\\u0600-\\u06FF]/g, "").slice(0, 3);
            digits = digits.replace(/[^0-9]/g, "").slice(0, 4);

            return {
                letters,
                digits,
                raw: t
            };
        }

        function showMatch(letters, digits) {
            const resultBox = document.getElementById("resultBox");
            const platesListDiv = document.getElementById("platesList");
            platesListDiv.innerHTML = "";

            const matches = plateDB.filter(p => p.letters === letters && p.digits === digits);

            resultBox.style.display = "block";

            if (matches.length === 0) {
                platesListDiv.innerHTML = '<div style="color: #dc3545; font-weight: bold;">❌ لا توجد لوحة مطابقة تماماً.</div>';
            } else {
                matches.forEach(p => {
                    const item = document.createElement("div");
                    item.className = "plate-item";
                    item.innerText = "📌 " + p.original;
                    platesListDiv.appendChild(item);
                });
                if ("vibrate" in navigator) navigator.vibrate(200);
            }
        }

        function autoMatchPlate(phrase) {
            if (!phrase) return;

            const extracted = extractPlateParts(phrase);

            document.getElementById("liveText").innerText = extracted.raw || "-";

            // لا نطابق إلا لو وصلنا بالضبط 3 حروف و 4 أرقام
            if (extracted.letters.length === 3 && extracted.digits.length === 4) {
                showMatch(extracted.letters, extracted.digits);
            }
        }

        function toggleSpeech() {
            if (!recognition) return;

            if (recognizing) {
                recognizing = false;
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (e) {
                    console.log(e);
                }
            }
        }

        function clearText() {
            document.getElementById("liveText").innerText = "-";
            document.getElementById("resultBox").style.display = "none";
            document.getElementById("platesList").innerHTML = "";
        }

        if (!SpeechRecognition) {
            document.getElementById("status").innerText = "المتصفح لا يدعم التحدث الصوتي.";
        } else {
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = "ar-EG";

            recognition.onstart = function() {
                recognizing = true;
                document.getElementById("status").innerText = "🎙️ يستمع الآن.. انطقي اللوحة بوضوح!";
                document.getElementById("toggleBtn").innerText = "⏹️ إيقاف الاستماع";
                document.getElementById("toggleBtn").className = "mic-btn stop-btn";
            };

            recognition.onerror = function(event) {
                console.log("Speech Error:", event.error);
                document.getElementById("status").innerText = "حدث خطأ في الميكروفون أو التعرف الصوتي.";
            };

            recognition.onend = function() {
                if (recognizing) {
                    try { recognition.start(); } catch(e) {}
                } else {
                    document.getElementById("status").innerText = "الميكروفون متوقف";
                    document.getElementById("toggleBtn").innerText = "🔴 تشغيل الاستماع";
                    document.getElementById("toggleBtn").className = "mic-btn start-btn";
                }
            };

            recognition.onresult = function(event) {
                let transcript = "";
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    transcript += event.results[i][0].transcript + " ";
                }
                transcript = transcript.trim();

                if (transcript) {
                    autoMatchPlate(transcript);
                }
            };
        }
    </script>
    """.replace("__DB__", db_json)

    st.components.v1.html(components_code, height=500)
