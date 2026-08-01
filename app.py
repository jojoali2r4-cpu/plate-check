import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="فحص اللوحات الدقيق", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 30px !important; font-weight: bold; text-align: center; padding: 20px; border-radius: 15px; margin-top: 15px; }
    .found-box { background-color: #f8d7da; color: #721c24; border: 3px solid #f5c6cb; }
    .not-found-box { background-color: #d4edda; color: #155724; border: 3px solid #c3e6cb; }
    .mic-btn { font-size: 20px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام فحص اللوحات (الالتقاط الحرفي المباشر)")
st.markdown("---")

def clean_plate(text):
    if not text:
        return ""
    text = str(text).strip()
    
    # تحويل الأرقام العربية إلى إنجليزية
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(arabic_digits, english_digits))
    
    # إزالة أي مسافات أو رموز خاصة والإبقاء على الحروف والأرقام فقط
    return re.sub(r'[^a-zA-Z0-9أ-ي]', '', text)

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)
    
    raw_plates = df[column_name].dropna().tolist()
    plate_set = set()
    plate_map = {}
    
    for plate in raw_plates:
        cleaned = clean_plate(plate)
        if cleaned:
            plate_set.add(cleaned)
            plate_map[cleaned] = str(plate)

    st.success(f"تم تحميل {len(plate_set)} لوحة جاهزة للفحص!")
    st.markdown("---")

    st.subheader("🎙️ الاستماع المباشر:")

    db_json = json.dumps(list(plate_set), ensure_ascii=False)
    map_json = json.dumps(plate_map, ensure_ascii=False)

    components_code = f"""
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 بدء الاستماع المستمر</button>
        <div id="status" style="margin-top: 10px; color: #888; font-size: 14px;">الميكروفون متوقف</div>
        
        <div style="margin-top: 20px;">
            <div style="font-size: 16px; color: #555;">المايك لقط بالضبط:</div>
            <div id="liveText" style="font-size: 32px; font-weight: bold; color: #007bff; min-height: 45px; margin: 10px 0;">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;"></div>
    </div>

    <script>
        const plateSet = new Set({db_json});
        const plateMap = {map_json};
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            document.getElementById('status').innerText = "المتصفح لا يدعم التحدث المباشر.";
        }} else {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA'; 

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ الميكروفون يعمل.. واصلي النطق طوالي!";
                document.getElementById('toggleBtn').innerText = "⏹️ إيقاف الاستماع";
                document.getElementById('toggleBtn').className = "mic-btn stop-btn";
            }};

            recognition.onend = function() {{
                if (recognizing) {{
                    recognition.start();
                }} else {{
                    document.getElementById('status').innerText = "الميكروفون متوقف";
                    document.getElementById('toggleBtn').innerText = "🔴 بدء الاستماع المستمر";
                    document.getElementById('toggleBtn').className = "mic-btn start-btn";
                }}
            }};

            recognition.onresult = function(event) {{
                let currentSpeech = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    currentSpeech = event.results[i][0].transcript;
                }}

                if (currentSpeech.trim() !== '') {{
                    document.getElementById('liveText').innerText = currentSpeech;
                    checkDirect(currentSpeech);
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

        function cleanString(str) {{
            if (!str) return "";
            // تحويل الأرقام الهندية لأرقام عالمية
            let t = str.replace(/[٠١٢٣٤٥٦٧٨٩]/g, function(d) {{ return d.charCodeAt(0) - 1632; }});
            // حذف كل المساحات والرموز
            return t.replace(/[^a-zA-Z0-9أ-ي]/g, '');
        }}

        function checkDirect(text) {{
            let cleaned = cleanString(text);
            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'block';

            if (!cleaned) return;

            // مطابقة مباشرة بالتعرف على النص الملتقط كما هو
            let isFound = false;
            let foundKey = "";

            if (plateSet.has(cleaned)) {{
                isFound = true;
                foundKey = cleaned;
            }} else {{
                // فحص إذا كان النص المنطوق يحتوى على أي لوحة من الملف
                for (let key of plateSet) {{
                    if (cleaned.includes(key) || key.includes(cleaned)) {{
                        isFound = true;
                        foundKey = key;
                        break;
                    }}
                }}
            }}

            if (isFound) {{
                let originalName = plateMap[foundKey] || foundKey;
                resultBox.className = 'status-box found-box';
                resultBox.innerHTML = '⚠️ اللوحة موجودة بالملف: (' + originalName + ')';
                
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
