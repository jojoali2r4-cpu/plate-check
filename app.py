import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="نظام فحص اللوحات الذكي المتطور", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; font-family: sans-serif; }
    .main-title { font-size: 26px; font-weight: bold; color: #1f4e78; text-align: center; margin-bottom: 20px; }
    .status-box { font-size: 20px; font-weight: bold; text-align: right; padding: 18px; border-radius: 12px; margin-top: 15px; }
    .box-found { background-color: #dcfce7; border: 3px solid #16a34a; color: #166534; }
    .box-not-found { background-color: #fee2e2; border: 3px solid #dc2626; color: #991b1b; text-align: center; }
    .mic-btn { font-size: 18px; padding: 14px 28px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; margin: 5px; width: 48%; transition: 0.3s; }
    .start-btn { background-color: #16a34a; color: white; }
    .stop-btn { background-color: #dc2626; color: white; }
    .clear-btn { background-color: #475569; color: white; }
    .interpreted-box { background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px; border-radius: 8px; margin-top: 10px; color: #1e40af; font-size: 20px; font-weight: bold; direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ نظام فحص اللوحات الذكي والمتطور بالصوت</div>', unsafe_allow_html=True)
st.markdown("---")

def parse_plate(text):
    if not text:
        return "", ""
    text = str(text).strip()
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(arabic_digits, english_digits))
    digits = "".join(re.findall(r'[0-9]', text))
    letters = "".join(re.findall(r'[\u0600-\u06FF]', text))
    return letters, digits

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)
    
    raw_plates = df[column_name].dropna().tolist()
    plate_database = []
    
    for plate in raw_plates:
        letters, digits = parse_plate(plate)
        if len(letters) >= 2 and len(digits) >= 2:
            plate_database.append({
                'original': str(plate).strip(),
                'letters': letters,
                'digits': digits
            })

    st.success(f"تم تحميل قاعدة بيانات اللوحات بنجاح ({len(plate_database)} لوحة صالحة)!")
    st.markdown("---")

    st.subheader("🎙️ محطة الفحص الصوتي المتقدم:")
    st.write("اضغط تشغيل وتحدث باللوحة بوضوح:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = """
    <div style="direction: rtl; text-align: center;">
        <div>
            <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع</button>
            <button class="mic-btn clear-btn" onclick="clearText()">🗑️ مسح النتائج</button>
        </div>
        
        <div id="status" style="margin-top: 10px; color: #475569; font-size: 15px; font-weight: bold;">الميكروفون متوقف</div>
        
        <div class="interpreted-box">
            <div style="font-size: 13px; color: #64748b; margin-bottom: 4px; text-align: right;">ما فهمه البرنامج من الصوت:</div>
            <div id="liveText" style="text-align: right;">-</div>
        </div>

        <div id="resultBox" style="display:none;" class="status-box">
            <div id="resultMessage"></div>
        </div>
    </div>

    <script>
        const plateDB = __DB_JSON__;
        let recognizing = false;
        let recognition = null;
        let lastSpokenText = "";

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            document.getElementById('status').innerText = "متصفحك لا يدعم التعرف الصوتي.";
        } else {
            try {
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.maxAlternatives = 10;
                recognition.lang = 'ar-SA';

                recognition.onstart = function() {
                    recognizing = true;
                    document.getElementById('status').innerText = "🎙️ جاري الاستماع.. تحدث الآن بوضوح!";
                    let btn = document.getElementById('toggleBtn');
                    btn.innerText = "⏹️ إيقاف الاستماع";
                    btn.className = "mic-btn stop-btn";
                };

                recognition.onerror = function(event) {
                    console.log("Speech Error event: ", event.error);
                };

                recognition.onend = function() {
                    if (recognizing) {
                        try { recognition.start(); } catch(e) {}
                    } else {
                        document.getElementById('status').innerText = "الميكروفون متوقف";
                        let btn = document.getElementById('toggleBtn');
                        btn.innerText = "🔴 تشغيل الاستماع";
                        btn.className = "mic-btn start-btn";
                    }
                };

                recognition.onresult = function(event) {
                    let bestInterpreted = "";

                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        let res = event.results[i];
                        for (let altIndex = 0; altIndex < res.length; altIndex++) {
                            let transcript = res[altIndex].transcript;
                            if (transcript) {
                                if (!bestInterpreted) bestInterpreted = transcript;
                            }
                        }
                    }

                    if (bestInterpreted && bestInterpreted !== lastSpokenText) {
                        lastSpokenText = bestInterpreted;
                        let processed = normalizeAndExtract(bestInterpreted);
                        
                        document.getElementById('liveText').innerText = processed.letters + " " + processed.digits;
                        checkAndDisplay(processed.letters, processed.digits);
                    }
                };
            } catch(e) {}
        }

        function toggleSpeech() {
            if (!recognition) return;
            if (recognizing) {
                recognizing = false;
                try { recognition.stop(); } catch(e) {}
            } else {
                lastSpokenText = "";
                try { recognition.start(); } catch(e) {}
            }
        }

        function clearText() {
            document.getElementById('liveText').innerText = "-";
            document.getElementById('resultBox').style.display = 'none';
            lastSpokenText = "";
        }

        function normalizeAndExtract(text) {
            let t = text;
            t = t.replace(/[٠-٩]/g, function(d) { return "٠١٢٣٤٥٦٧٨٩".indexOf(d); });
            
            t = t.replace(/صفر|صيف/g, "0")
                 .replace(/واحد|واحده/g, "1")
                 .replace(/اتنين|ثثنين|اثنين|تنين/g, "2")
                 .replace(/تلاتة|ثلاثة|تلات/g, "3")
                 .replace(/اربعة|أربعة|اربعه|ربع/g, "4")
                 .replace(/خمسة|خمسه|خمس/g, "5")
                 .replace(/سته|ستة|ست/g, "6")
                 .replace(/سبعة|سبعه|سبع/g, "7")
                 .replace(/تمانية|ثمانية|ثامنه|تمنيه|ثمان/g, "8")
                 .replace(/تسعة|تسعه|تسع/g, "9");

            t = t.replace(/حسين|حسن|حسون|سين|سني/g, "س")
                 .replace(/رقية|رقبه|راء|رائيه/g, "ر")
                 .replace(/بهاء|باها|باء|بائيه/g, "ب")
                 .replace(/زين|زينة|زاي/g, "ز")
                 .replace(/شيماء|شيم|شين/g, "ش")
                 .replace(/صالح|صلح|صاد/g, "ص")
                 .replace(/محمد|محمده|ميم/g, "م")
                 .replace(/علي|علا|عين/g, "ع")
                 .replace(/خالد|خلد|خاء/g, "خ")
                 .replace(/ناصر|نصر|نون/g, "ن")
                 .replace(/تيسير|يسير|تاء/g, "ت")
                 .replace(/قاسم|قسم|قاف/g, "ق")
                 .replace(/الف|ألف/g, "أ")
                 .replace(/دال|دولة/g, "د")
                 .replace(/جيم|جمل/g, "ج")
                 .replace(/هاء|هوا/g, "ه")
                 .replace(/واو/g, "و")
                 .replace(/لام/g, "ل")
                 .replace(/طاس|طاء/g, "ط");

            let rawLetters = (t.match(/[\\u0600-\\u06FF]/g) || []).join("").replace(/\\s+/g, '');
            let letters = rawLetters.length > 3 ? rawLetters.substring(0, 3) : rawLetters;

            let digits = (t.match(/[0-9]/g) || []).join("");
            if (digits.length > 4) {
                digits = digits.substring(0, 4);
            }

            return { letters: letters, digits: digits };
        }

        function checkAndDisplay(inputLetters, inputDigits) {
            let resultBox = document.getElementById('resultBox');
            let resultMsg = document.getElementById('resultMessage');

            if (inputLetters.length < 2 || inputDigits.length < 2) {
                resultBox.style.display = 'none';
                return;
            }

            let matches = [];
            plateDB.forEach(function(p) {
                let lMatch = (p.letters.includes(inputLetters) || inputLetters.includes(p.letters) || levenshtein(p.letters, inputLetters) <= 1);
                let dMatch = (p.digits === inputDigits || p.digits.includes(inputDigits) || inputDigits.includes(p.digits));

                if (lMatch && dMatch) {
                    matches.push(p.original);
                }
            });

            let uniqueMatches = [...new Set(matches)];

            if (uniqueMatches.length > 0) {
                // موجودة: تلوين بالأخضر + اهتزاز قوية جداً ومكررة
                resultBox.className = "status-box box-found";
                resultMsg.innerHTML = "✅ موجودة: " + uniqueMatches.join(" - ");
                resultBox.style.display = 'block';
                if ("vibrate" in navigator) { 
                    navigator.vibrate([400, 200, 400]); 
                }
            } else {
                // غير موجودة: تلوين بالأحمر فقط بدون اهتزاز
                resultBox.className = "status-box box-not-found";
                resultMsg.innerHTML = "❌ غير موجودة في الملف";
                resultBox.style.display = 'block';
            }
        }

        function levenshtein(a, b) {
            if(a.length === 0) return b.length;
            if(b.length === 0) return a.length;
            let matrix = [];
            let i, j;
            for(i = 0; i <= b.length; i++) { matrix[i] = [i]; }
            for(j = 0; j <= a.length; j++) { matrix[0][j] = j; }
            for(i = 1; i <= b.length; i++) {
                for(j = 1; j <= a.length; j++) {
                    if(b.charAt(i-1) == a.charAt(j-1)) {
                        matrix[i][j] = matrix[i-1][j-1];
                    } else {
                        matrix[i][j] = Math.min(matrix[i-1][j-1] + 1, Math.min(matrix[i][j-1] + 1, matrix[i-1][j] + 1));
                    }
                }
            }
            return matrix[b.length][a.length];
        }
    </script>
    """

    components_code = components_code.replace("__DB_JSON__", db_json)
    st.components.v1.html(components_code, height=500)
