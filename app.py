import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="نظام فحص اللوحات الذكي المتطور", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; font-family: sans-serif; }
    .main-title { font-size: 26px; font-weight: bold; color: #1f4e78; text-align: center; margin-bottom: 20px; }
    .status-box { font-size: 18px; font-weight: bold; text-align: right; padding: 15px; border-radius: 12px; margin-top: 15px; background-color: #f1f5f9; border: 2px solid #cbd5e1; color: #1e293b; }
    .mic-btn { font-size: 18px; padding: 14px 28px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; margin: 5px; width: 48%; transition: 0.3s; }
    .start-btn { background-color: #16a34a; color: white; }
    .stop-btn { background-color: #dc2626; color: white; }
    .clear-btn { background-color: #475569; color: white; }
    .plate-item { background: #dcfce7; border: 1px solid #86efac; padding: 14px; margin: 8px 0; border-radius: 8px; font-weight: bold; color: #166534; font-size: 26px; text-align: center; }
    .interpreted-box { background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px; border-radius: 8px; margin-top: 10px; color: #1e40af; font-size: 20px; font-weight: bold; }
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
        if len(letters) == 3 and len(digits) == 4:
            plate_database.append({
                'original': str(plate).strip(),
                'letters': letters,
                'digits': digits
            })

    st.success(f"تم تحميل وقهر قاعدة بيانات اللوحات بنجاح ({len(plate_database)} لوحة صالحة)!")
    st.markdown("---")

    st.subheader("🎙️ محطة الفحص الصوتي المتقدم (maxAlternatives = 10):")
    st.write("اضغط تشغيل وتحدث باللوحة بوضوح (حروف وأرقام):")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = f"""
    <div style="direction: rtl; text-align: center;">
        <div>
            <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع</button>
            <button class="mic-btn clear-btn" onclick="clearText()">🗑️ مسح النتائج</button>
        </div>
        
        <div id="status" style="margin-top: 10px; color: #475569; font-size: 15px; font-weight: bold;">الميكروفون متوقف</div>
        
        <div class="interpreted-box">
            <div style="font-size: 13px; color: #64748b; margin-bottom: 4px;">ما فهمه البرنامج من البدائل الصوتية:</div>
            <div id="liveText">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;">
            <div style="font-weight: bold; margin-bottom: 8px; color: #0f172a;">📌 اللوحات المطابقة بالملف:</div>
            <div id="platesList"></div>
        </div>
    </div>

    <script>
        const plateDB = """ + db_json + """;
        let recognizing = false;
        let recognition;
        let lastFoundPlate = "";

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            document.getElementById('status').innerText = "متصفحك لا يدعم التعرف الصوتي المتقدم.";
        } else {
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.maxAlternatives = 10;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ جاري الاستماع بجميع البدائل المتاحة.. تحدث الآن!";
                document.getElementById('toggleBtn').innerText = "⏹️ إيقاف الاستماع";
                document.getElementById('toggleBtn').className = "mic-btn stop-btn";
            };

            recognition.onerror = function(event) {
                console.log("Speech Error: ", event.error);
            };

            recognition.onend = function() {
                if (recognizing) {
                    try { recognition.start(); } catch(e) {}
                } else {
                    document.getElementById('status').innerText = "الميكروفون متوقف";
                    document.getElementById('toggleBtn').innerText = "🔴 تشغيل الاستماع";
                    document.getElementById('toggleBtn').className = "mic-btn start-btn";
                }
            };

            recognition.onresult = function(event) {
                let bestInterpreted = "";
                let matchedResults = [];

                // فحص جميع النتائج والبدائل (maxAlternatives) في كل حزمة صوتية
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    let res = event.results[i];
                    for (let altIndex = 0; altIndex < res.length; altIndex++) {
                        let transcript = res[altIndex].transcript;
                        if (transcript) {
                            if (!bestInterpreted) bestInterpreted = transcript; // حفظ أول بديل للعرض
                            let processed = normalizeAndExtract(transcript);
                            let found = smartMatch(processed.letters, processed.digits);
                            if (found.length > 0) {
                                matchedResults = matchedResults.concat(found);
                            }
                        }
                    }
                }

                if (bestInterpreted) {
                    document.getElementById('liveText').innerText = bestInterpreted;
                }

                // إزالة التكرار للوحات المكتشفة
                let uniquePlates = [...new Set(matchedResults)];
                if (uniquePlates.length > 0) {
                    displayResults(uniquePlates);
                }
            };
        }

        function toggleSpeech() {
            if (recognizing) {
                recognizing = false;
                recognition.stop();
            } else {
                lastFoundPlate = "";
                try {
                    recognition.start();
                } catch(e) {
                    console.log(e);
                }
            }
        }

        function clearText() {
            document.getElementById('liveText').innerText = "-";
            document.getElementById('resultBox').style.display = 'none';
            lastFoundPlate = "";
        }

        function normalizeAndExtract(text) {
            let t = text;
            // توحيد الأرقام
            t = t.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
            
            // قاموس تصحيح الأرقام المنطوقة لفظياً
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

            // قاموس تصحيح الحروف والأسماء الشائعة التي يخطئ فيها المحرك
            t = t.replace(/حسين|حسن|حسون/g, "س")
                 .replace(/رقية|رقبه|رقية/g, "ر")
                 .replace(/بهاء|باها/g, "ب")
                 .replace(/زين|زينة/g, "ز")
                 .replace(/شيماء|شيم/g, "ش")
                 .replace(/صالح|صلح/g, "ص")
                 .replace(/محمد|محمده/g, "م")
                 .replace(/علي|علا/g, "ع")
                 .replace(/خالد|خلد/g, "خ")
                 .replace(/ناصر|نصر/g, "ن")
                 .replace(/تيسير|يسير/g, "ت")
                 .replace(/قاسم|قسم/g, "ق");

            // استخراج وتجميع الحروف والأرقام بدقة وحفظ الترتيب
            let letters = (t.match(/[\\u0600-\\u06FF]/g) || []).join("").replace(/\\s+/g, '');
            let digits = (t.match(/[0-9]/g) || []).join("");

            if (letters.length > 3) letters = letters.substring(0, 3);
            if (digits.length > 4) digits = digits.substring(0, 4);

            return {{ letters: letters, digits: digits }};
        }

        // دالة المطابقة الذكية (تسمح بخطأ بسيط بحد أقصى حرف أو رقم للوصول للنتيجة)
        function smartMatch(inputLetters, inputDigits) {{
            let matches = [];
            if (inputLetters.length >= 2 && inputDigits.length === 4) {{
                plateDB.forEach(p => {{
                    let lMatch = (p.letters === inputLetters) || (levenshtein(p.letters, inputLetters) <= 1);
                    let dMatch = (p.digits === inputDigits); // منع قلب أو تغيير الأرقام تماماً كما طلب
                    if (lMatch && dMatch) {{
                        matches.push(p.original);
                    }}
                }});
            }}
            return matches;
        }}

        // حساب المسافة لفلترة التطابق البسيط (Fuzzy)
        function levenshtein(a, b) {{
            if(a.length === 0) return b.length;
            if(b.length === 0) return a.length;
            let matrix = [];
            let i, j;
            for(i = 0; i <= b.length; i++) {{ matrix[i] = [i]; }}
            for(j = 0; j <= a.length; j++) {{ matrix[0][j] = j; }}
            for(i = 1; i <= b.length; i++) {{
                for(j = 1; j <= a.length; j++) {{
                    if(b.charAt(i-1) == a.charAt(j-1)) {{
                        matrix[i][j] = matrix[i-1][j-1];
                    }} else {{
                        matrix[i][j] = Math.min(matrix[i-1][j-1] + 1, Math.min(matrix[i][j-1] + 1, matrix[i-1][j] + 1));
                    }}
                }}
            }}
            return matrix[b.length][a.length];
        }}

        function displayResults(plates) {{
            let plateStr = plates.join(",");
            if (plateStr === lastFoundPlate) return; // منع تكرار نفس اللوحة أثناء الاستماع المستمر
            lastFoundPlate = plateStr;

            let resultBox = document.getElementById('resultBox');
            let platesListDiv = document.getElementById('platesList');
            platesListDiv.innerHTML = "";

            plates.forEach(plate => {{
                let item = document.createElement('div');
                item.className = 'plate-item';
                item.innerText = '📌 ' + plate;
                platesListDiv.appendChild(item);
            }});

            resultBox.style.display = 'block';
            if ("vibrate" in navigator) {{ navigator.vibrate(250); }}
        }}
    </script>
    """

    st.components.v1.html(components_code, height=500)
