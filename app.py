import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="فحص اللوحات الذكي الفوري", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 26px !important; font-weight: bold; text-align: center; padding: 18px; border-radius: 12px; margin-top: 15px; }
    .found-box { background-color: #f8d7da; color: #721c24; border: 3px solid #f5c6cb; }
    .not-found-box { background-color: #d4edda; color: #155724; border: 3px solid #c3e6cb; }
    .mic-btn { font-size: 18px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; margin: 5px; width: 48%; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    .clear-btn { background-color: #6c757d; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام فحص اللوحات الفوري (النسخة الخارقة المحدثة)")
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
            'original': str(plate),
            'letters': letters,
            'digits': digits
        })

    st.success(f"تم تحميل {len(plate_database)} لوحة بنجاح!")
    st.markdown("---")

    st.subheader("🎙️ الفحص الصوتي الفوري:")
    st.write("اضغطي على زر التشغيل وانطقي اللوحة مباشرة:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = f"""
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع</button>
        <button id="clearBtn" class="mic-btn clear-btn" onclick="clearText()">🗑️ مسح النص</button>
        
        <div id="status" style="margin-top: 10px; color: #666; font-size: 14px;">الميكروفون متوقف</div>
        
        <div style="margin-top: 15px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <div style="font-size: 14px; color: #555;">النص الملتقط لحظياً:</div>
            <div id="liveText" style="font-size: 26px; font-weight: bold; color: #007bff; min-height: 35px;">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;"></div>
    </div>

    <script>
        const plateDB = {db_json};
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            document.getElementById('status').innerText = "المتصفح لا يدعم التحدث الصوتي.";
        }} else {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ يستمع الآن.. انطقي بسرعة!";
                document.getElementById('toggleBtn').innerText = "⏹️ إيقاف الاستماع";
                document.getElementById('toggleBtn').className = "mic-btn stop-btn";
            }};

            recognition.onerror = function(event) {{
                console.log("Speech Error: ", event.error);
            }};

            recognition.onend = function() {{
                if (recognizing) {{
                    try {{ recognition.start(); }} catch(e) {{}}
                }} else {{
                    document.getElementById('status').innerText = "الميكروفون متوقف";
                    document.getElementById('toggleBtn').innerText = "🔴 تشغيل الاستماع";
                    document.getElementById('toggleBtn').className = "mic-btn start-btn";
                }}
            }};

            recognition.onresult = function(event) {{
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    if (event.results[i].isFinal) {{
                        finalTranscript += event.results[i][0].transcript;
                    }} else {{
                        interimTranscript += event.results[i][0].transcript;
                    }}
                }}

                let currentText = finalTranscript || interimTranscript;
                if (currentText.trim() !== "") {{
                    document.getElementById('liveText').innerText = currentText;
                    matchUltimateEngine(currentText);
                }}
            }};
        }}

        function toggleSpeech() {{
            if (recognizing) {{
                recognizing = false;
                recognition.stop();
            }} else {{
                try {{
                    recognition.start();
                }} catch(e) {{
                    console.log(e);
                }}
            }}
        }}

        function clearText() {{
            document.getElementById('liveText').innerText = "-";
            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'none';
        }}

        function matchUltimateEngine(phrase) {{
            let t = phrase;
            
            // تحويل الأرقام العربية الهندية إلى إنجليزية
            t = t.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
            
            // تحويل الكلمات المنطوقة للأرقام إلى قيم رقمية
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

            // توحيد الحروف مهما كتبها المتصفح (بسلام، بصل، باسيل، إلخ)
            t = t.replace(/بسلام|باسلام|بصل|باسيل|بأسين|باسين|باء سين|با سين|باء سين لام|باسين لام|بس ل|افلام|أفلام/g, "بسل");

            // استخراج جميع الأرقام الموجودة في النص وترتيبها تصاعدياً لتجاوز مشكلة تبديل الخانات نهائياً
            let inputDigitsArray = t.match(/[0-9]/g) || [];
            let inputDigitsSorted = inputDigitsArray.sort().join("");
            
            // استخراج وتصفية الحروف
            let inputLetters = (t.match(/[\\u0600-\\u06FF]/g) || []).join("").replace(/\\s+/g, '');
            inputLetters = inputLetters.replace(/[اأإآىيؤئةو]/g, '');

            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'block';

            let matched = null;

            plateDB.forEach(p => {{
                let targetDigitsArray = p.digits ? p.digits.split('') : [];
                let targetDigitsSorted = targetDigitsArray.sort().join("");
                
                let cleanTargetLetters = p.letters ? p.letters.replace(/\\s+/g, '').replace(/[اأإآىيؤئةو]/g, '') : "";

                // المطابقة النهائية للأرقام (بترتيب مرن) والحروف (بشكل شامل)
                let digitsMatch = (inputDigitsSorted !== "" && inputDigitsSorted === targetDigitsSorted);
                let lettersMatch = (inputLetters.includes("بسل".replace(/[اأإآىيؤئةو]/g, '')) && cleanTargetLetters.includes("بسل".replace(/[اأإآىيؤئةو]/g, ''))) || (inputLetters === cleanTargetLetters) || (cleanTargetLetters === "" && inputLetters === "");

                if (digitsMatch && lettersMatch) {{
                    matched = p;
                }}
            }});

            if (matched) {{
                resultBox.className = 'status-box found-box';
                resultBox.innerHTML = '⚠️ اللوحة موجودة بالملف: (' + matched.original + ')';
                if ("vibrate" in navigator) {{ navigator.vibrate([300, 100, 300]); }}
                playBeep();
            }} else {{
                resultBox.className = 'status-box not-found-box';
                resultBox.innerHTML = '✅ غير موجودة';
            }}
        }}

        function playBeep() {{
            try {{
                var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                var osc = audioCtx.createOscillator();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880, audioCtx.currentTime);
                osc.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.3);
            }} catch(e) {{}}
        }}
    </script>
    """

    st.components.v1.html(components_code, height=380)
