import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="فحص اللوحات الذكي", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 26px !important; font-weight: bold; text-align: center; padding: 18px; border-radius: 12px; margin-top: 15px; }
    .found-box { background-color: #f8d7da; color: #721c24; border: 3px solid #f5c6cb; }
    .not-found-box { background-color: #d4edda; color: #155724; border: 3px solid #c3e6cb; }
    .mic-btn { font-size: 18px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; width: 100%; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام فحص اللوحات الذكي (مضاد تبديل الأرقام)")
st.caption("يتعامل بذكاء مع تبديل المتصفح للأرقام الصوتية")
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

    st.subheader("🎙️ الفحص الصوتي المباشر:")
    st.write("اضغطي على الزر وانطقي اللوحة:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = f"""
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع</button>
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
                document.getElementById('status').innerText = "🎙️ يستمع الآن.. انطقي اللوحة!";
                document.getElementById('toggleBtn').innerText = "⏹️ إيقاف الاستماع";
                document.getElementById('toggleBtn').className = "mic-btn stop-btn";
            }};

            recognition.onerror = function(event) {{
                console.log("Speech Recognition Error: ", event.error);
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
                let fullTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    fullTranscript += event.results[i][0].transcript;
                }}

                if (fullTranscript.trim() !== '') {{
                    document.getElementById('liveText').innerText = fullTranscript;
                    matchSmart(fullTranscript);
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

        function normalizeArabicLetters(text) {{
            let t = text;
            t = t.replace(/أفلام|افلام|بصل/g, "بسل")
                 .replace(/ألف|الف/g, "أ")
                 .replace(/باء|با/g, "ب")
                 .replace(/تاء|تا/g, "ت")
                 .replace(/ثاء|ثا/g, "ث")
                 .replace(/جيم/g, "ج")
                 .replace(/حاء|حا/g, "ح")
                 .replace(/خاء|خا/g, "خ")
                 .replace(/دال/g, "د")
                 .replace(/ذال/g, "ذ")
                 .replace(/راء|را/g, "ر")
                 .replace(/زاي|زين/g, "ز")
                 .replace(/سين/g, "س")
                 .replace(/شين/g, "ش")
                 .replace(/صاد/g, "ص")
                 .replace(/ضاد/g, "ض")
                 .replace(/طاء|طا/g, "ط")
                 .replace(/ظاء|ظا/g, "ظ")
                 .replace(/عين/g, "ع")
                 .replace(/غين/g, "غ")
                 .replace(/فاء|فا/g, "ف")
                 .replace(/قاف/g, "ق")
                 .replace(/كاف/g, "ك")
                 .replace(/لام/g, "ل")
                 .replace(/ميم/g, "م")
                 .replace(/نون/g, "ن")
                 .replace(/هاء|ها/g, "هـ")
                 .replace(/واو/g, "و")
                 .replace(/ياء|يا|ياسين/g, "ي");
            return t;
        }}

        function matchSmart(phrase) {{
            let converted = phrase.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
            let digits = (converted.match(/[0-9]/g) || []).join("");
            
            let letterText = normalizeArabicLetters(converted);
            let letters = (letterText.match(/[\u0600-\u06FF]/g) || []).join("").replace(/\s+/g, '');

            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'block';

            let matched = null;

            // 1. المطابقة الدقيقة بالأرقام والحروف معاً
            if (digits && letters) {{
                matched = plateDB.find(p => p.digits === digits && (p.letters.includes(letters) || letters.includes(p.letters)));
            }}
            
            // 2. المطابقة بالأرقام التامة
            if (!matched && digits.length >= 3) {{
                matched = plateDB.find(p => p.digits === digits);
            }}

            // 3. الحل الذكي لتبديل الأرقام: مطابقة الأرقام بغض النظر عن الترتيب (مثل 4674 تطابق 4764)
            if (!matched && digits.length >= 3) {{
                let sortedInputDigits = digits.split('').sort().join('');
                matched = plateDB.find(p => p.digits.split('').sort().join('') === sortedInputDigits);
            }}

            // 4. المطابقة بالحروف فقط (لو لم تُقرأ الأرقام بدقة)
            if (!matched && letters.length >= 2) {{
                matched = plateDB.find(p => p.letters === letters || p.original.includes(letters));
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
