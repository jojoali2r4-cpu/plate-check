import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="فحص اللوحات السريع", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 32px !important; font-weight: bold; text-align: center; padding: 25px; border-radius: 15px; margin-top: 15px; }
    .found-box { background-color: #f8d7da; color: #721c24; border: 3px solid #f5c6cb; }
    .not-found-box { background-color: #d4edda; color: #155724; border: 3px solid #c3e6cb; }
    .live-speech-container { background: #1e1e1e; padding: 20px; border-radius: 10px; color: #fff; text-align: center; margin: 20px 0; }
    .mic-btn { font-size: 20px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام الفحص والإملاء الفوري السريع")
st.markdown("---")

def clean_text(text):
    if not text:
        return ""
    text = str(text).strip()
    replacements = {
        'الف': '1000', 'ألف': '1000', 'واحد': '1', 'ثنين': '2', 'ثلاثه': '3', 
        'اربعة': '4', 'خمسة': '5', 'ستة': '6', 'سبعة': '7', 'ثمانية': '8', 'تسعة': '9'
    }
    for word, num in replacements.items():
        text = text.replace(word, num)
    return re.sub(r'\s+', '', text)

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)
    
    # تحضير قائمة اللوحات المنظفة
    existing_plates = [clean_text(x) for x in df[column_name].dropna().tolist()]
    existing_plates_set = set(existing_plates) # لاستعلام فوري بـ O(1)
    
    st.success(f"تم تحميل الملف! عدد اللوحات: {len(existing_plates)}")
    st.markdown("---")

    st.subheader("🎙️ الاستماع الفوري المستمر:")
    st.write("اضغط زر التفعيل مرة واحدة، ثم واصل نطق اللوحات ورا بعض بدون توقف!")

    # تضمين نظام الاستماع المباشر عالي السرعة عبر JavaScript
    plates_json = str(list(existing_plates_set))

    components_code = f"""
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 بدء الاستماع المستمر</button>
        <div id="status" style="margin-top: 10px; color: #888; font-size: 14px;">الميكروفون متوقف</div>
        
        <div style="margin-top: 20px;">
            <div style="font-size: 16px; color: #555;">اللوحة المنطوقة حالياً:</div>
            <div id="liveText" style="font-size: 28px; font-weight: bold; color: #007bff; min-height: 40px; margin: 10px 0;">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;"></div>
    </div>

    <script>
        const existingPlates = new Set({plates_json});
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            document.getElementById('status').innerText = "متصفحك لا يدعم التعرف الصوتي المباشر. استخدم Chrome على Android.";
        }} else {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ الميكروفون يعمل الآن.. واصل نطق اللوحات مباشرة!";
                document.getElementById('toggleBtn').innerText = "⏹️ إيقاف الاستماع";
                document.getElementById('toggleBtn').className = "mic-btn stop-btn";
            }};

            recognition.onend = function() {{
                if (recognizing) {{
                    recognition.start(); // إعادة التشغيل التلقائي إذا توقف المتصفح لحظياً
                }} else {{
                    document.getElementById('status').innerText = "الميكروفون متوقف";
                    document.getElementById('toggleBtn').innerText = "🔴 بدء الاستماع المستمر";
                    document.getElementById('toggleBtn').className = "mic-btn start-btn";
                }}
            }};

            recognition.onresult = function(event) {{
                let interimTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    interimTranscript += event.results[i][0].transcript;
                }}

                if (interimTranscript.trim() !== '') {{
                    let rawText = interimTranscript.trim();
                    // أخذ آخر كلمة/لوحة منطوقة لسرعة الفحص
                    let words = rawText.split(' ');
                    let lastSpeech = words[words.length - 1];

                    document.getElementById('liveText').innerText = rawText;

                    checkPlate(lastSpeech, rawText);
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

        function cleanText(text) {{
            return text.replace(/\\s+/g, '').replace(/ألف|الف/g, '1000');
        }}

        function checkPlate(lastWord, fullText) {{
            let cleanedLast = cleanText(lastWord);
            let cleanedFull = cleanText(fullText);

            let isFound = existingPlates.has(cleanedLast) || existingPlates.has(cleanedFull);
            let resultBox = document.getElementById('resultBox');

            resultBox.style.display = 'block';

            if (isFound) {{
                resultBox.className = 'status-box found-box';
                resultBox.innerHTML = '⚠️ اللوحة (' + fullText + ') : موجودة في الملف!';
                
                // تنبيه اهتزاز وصوت فوراً
                if ("vibrate" in navigator) {{ navigator.vibrate([300, 100, 300]); }}
                playBeep();
            }} else {{
                resultBox.className = 'status-box not-found-box';
                resultBox.innerHTML = '✅ اللوحة (' + fullText + ') : غير موجودة';
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
