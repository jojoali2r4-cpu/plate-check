import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="فحص اللوحات الذكي المجاني", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 28px !important; font-weight: bold; text-align: center; padding: 20px; border-radius: 15px; margin-top: 15px; }
    .found-box { background-color: #f8d7da; color: #721c24; border: 3px solid #f5c6cb; }
    .not-found-box { background-color: #d4edda; color: #155724; border: 3px solid #c3e6cb; }
    .mic-btn { font-size: 20px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; width: 100%; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام فحص اللوحات المباشر")
st.caption("مطابقة فائقة الذكاء للأرقام والحروف الصوتية")
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
        if digits:
            plate_database.append({
                'original': str(plate),
                'letters': letters,
                'digits': digits
            })

    st.success(f"تم تحميل {len(plate_database)} لوحة بنجاح!")
    st.markdown("---")

    st.subheader("🎙️ الفحص الصوتي المباشر:")
    st.write("اضغطي على الزر وانطقي اللوحة:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = f"""
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع المستمر</button>
        <div id="status" style="margin-top: 10px; color: #666; font-size: 14px;">الميكروفون متوقف</div>
        
        <div style="margin-top: 15px; background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <div style="font-size: 14px; color: #555;">النص الملتقط:</div>
            <div id="liveText" style="font-size: 24px; font-weight: bold; color: #007bff; min-height: 35px;">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;"></div>
    </div>

    <script>
        const plateDB = {db_json};
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            document.getElementById('status').innerText = "المتصفح لا يدعم التحدث الصوتي المباشر.";
        }} else {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ الميكروفون يستمع الآن.. انطقي اللوحة!";
                document.getElementById('toggleBtn').innerText = "⏹️ إيقاف الاستماع";
                document.getElementById('toggleBtn').className = "mic-btn stop-btn";
            }};

            recognition.onend = function() {{
                if (recognizing) {{
                    recognition.start();
                }} else {{
                    document.getElementById('status').innerText = "الميكروفون متوقف";
                    document.getElementById('toggleBtn').innerText = "🔴 تشغيل الاستماع المستمر";
                    document.getElementById('toggleBtn').className = "mic-btn start-btn";
                }}
            }};

            recognition.onresult = function(event) {{
                let lastPhrase = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    lastPhrase = event.results[i][0].transcript;
                }}

                if (lastPhrase.trim() !== '') {{
                    document.getElementById('liveText').innerText = lastPhrase;
                    matchSmart(lastPhrase);
                }}
            }};
        }}

        function toggleSpeech() {{
            if (recognizing) {{
                recognizing = false;
                recognition.stop();
            }} else {{
                recognition.start();
            }}
        }}

        function matchSmart(phrase) {{
            // تحويل الأرقام العربية إلى إنجليزية
            let converted = phrase.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
            
            // استخراج الأرقام المعثور عليها
            let digitsArray = converted.match(/[0-9]/g) || [];
            let digits = digitsArray.join("");

            let resultBox = document.getElementById('resultBox');
            if (digitsArray.length < 3) return; // الانتظار لحين نطق معظم الأرقام

            resultBox.style.display = 'block';

            // البحث الذكي: مطابقة بالأرقام كاملة أو مع ترتيب الأرقام
            let matched = plateDB.find(p => p.digits === digits);

            // لو المتصفح عكس رقمين (مثل 4674 بدلاً من 4764)، نقارن بوجود أرقام اللوحة نفسها
            if (!matched && digitsArray.length >= 4) {{
                let sortedInput = digitsArray.slice().sort().join("");
                matched = plateDB.find(p => p.digits.split('').sort().join("") === sortedInput);
            }}

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

    st.components.v1.html(components_code, height=350)
