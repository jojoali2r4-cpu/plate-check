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
        plate_database.append({
            'original': str(plate).strip(),
            'letters': letters,
            'digits': digits
        })

    st.success(f"تم تحميل {len(plate_database)} لوحة بنجاح!")
    st.markdown("---")

    st.subheader("🎙️ الفحص الصوتي التلقائي:")
    st.write("اضغطي على زر التشغيل وانطقي اللوحة مباشرة ليتم جلب مطابقتها تلقائياً:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = f"""
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
        const plateDB = """ + db_json + """;
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            document.getElementById('status').innerText = "المتصفح لا يدعم التحدث الصوتي.";
        } else {
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ يستمع الآن.. انطقي اللوحة بوضوح!";
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
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                let currentText = finalTranscript || interimTranscript;
                if (currentText.trim() !== "") {
                    document.getElementById('liveText').innerText = currentText;
                    autoMatchPlate(currentText);
                }
            };
        }

        function toggleSpeech() {
            if (recognizing) {
                recognizing = false;
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch(e) {
                    console.log(e);
                }
            }
        }

        function clearText() {
            document.getElementById('liveText').innerText = "-";
            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'none';
        }

        function autoMatchPlate(phrase) {
            let t = phrase;
            if (!t) return;
            
            // تحويل الأرقام العربية إلى إنجليزية
            t = t.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
            
            // مطابقة الأرقام المنطوقة لفظياً بالترتيب
            t = t.replace(/صفر/g, "0")
                 .replace(/واحد/g, "1")
                 .replace(/اتنين|ثثنين|اثنين/g, "2")
                 .replace(/تلاتة|ثلاثة|تلات/g, "3")
                 .replace(/اربعة|أربعة|اربعه|ربع/g, "4")
                 .replace(/خمسة|خمسه/g, "5")
                 .replace(/سته|ستة|ست/g, "6")
                 .replace(/سبعة|سبعه/g, "7")
                 .replace(/تمانية|ثمانية|ثامنه|تمنيه|ثمان/g, "8")
                 .replace(/تسعة|تسعه|تسع/g, "9");

            // استخراج الأرقام والحفاظ على ترتيبها الأصلي تماماً
            let inputDigits = (t.match(/[0-9]/g) || []).join("");
            
            // استخراج الحروف فقط وإزالة المسافات بينها مع الحفاظ على الترتيب الأصلي
            let inputLetters = (t.match(/[\\u0600-\\u06FF]/g) || []).join("").replace(/\\s+/g, '');

            let resultBox = document.getElementById('resultBox');
            let platesListDiv = document.getElementById('platesList');
            platesListDiv.innerHTML = "";

            let matchedCount = 0;

            plateDB.forEach(p => {
                let targetDigits = p.digits ? p.digits : "";
                let targetLetters = p.letters ? p.letters.replace(/\\s+/g, '') : "";

                // مطابقة دقيقة بالترتيب الأصلي للحروف والأرقام
                let digitsMatch = (inputDigits !== "" && targetDigits.includes(inputDigits));
                let lettersMatch = (inputLetters !== "" && targetLetters.includes(inputLetters));

                if (digitsMatch && lettersMatch) {
                    matchedCount++;
                    let item = document.createElement('div');
                    item.className = 'plate-item';
                    item.innerText = '📌 ' + p.original;
                    platesListDiv.appendChild(item);
                }
            });

            resultBox.style.display = 'block';
            if (matchedCount === 0) {
                platesListDiv.innerHTML = '<div style="color: #dc3545; font-weight: bold;">❌ لا توجد لوحة مطابقة بالملف.</div>';
            } else {
                if ("vibrate" in navigator) { navigator.vibrate(200); }
            }
        }
    </script>
    """

    st.components.v1.html(components_code, height=450)
