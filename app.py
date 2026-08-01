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
    .mic-btn { font-size: 18px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; margin: 5px; width: 48%; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    .clear-btn { background-color: #6c757d; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام فحص اللوحات الفوري (النسخة النهائية)")
st.caption("إلغاء قيود ترتيب الأرقام ودمج الحروف المنفصلة تلقائياً")
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
        <button id="clearBtn" class="mic-btn clear-btn" onclick="clearText()">🗑️ مسح النص</button>
        
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
            recognition.interimResults = false;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ يستمع الآن.. انطقي اللوحة!";
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
                let lastIndex = event.results.length - 1;
                let text = event.results[lastIndex][0].transcript.trim();

                if (text !== "") {{
                    document.getElementById('liveText').innerText = text;
                    matchFuzzy(text);
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

        function matchFuzzy(phrase) {{
            // تحويل الأرقام العربية الهندية إلى إنجليزية
            let converted = phrase.replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));
            
            // استخراج الأرقام وحدها وترتيبها لتلافي خطأ الترتيب أو التبديل
            let inputDigits = (converted.match(/[0-9]/g) || []).sort().join("");
            
            // استخراج جميع الحروف العربية وإزالة كافة المسافات بينها لضمان دمجها
            let inputLetters = (converted.match(/[\u0600-\u06FF]/g) || []).join("").replace(/\\s+/g, '');

            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'block';

            let matched = null;

            plateDB.forEach(p => {{
                let lettersMatch = false;
                let digitsMatch = false;

                // مطابقة الحروف المرنة (إذا كانت الحروف المنطوقة جزءاً من حروف اللوحة أو العكس)
                if (!inputLetters || inputLetters.length === 0) {{
                    lettersMatch = true;
                }} else if (p.letters) {{
                    let targetLettersSorted = p.letters.split('').sort().join('');
                    let inputLettersSorted = inputLetters.split('').sort().join('');
                    
                    // إذا تقاطعت الحروف أو تداخلت
                    if (targetLettersSorted.includes(inputLetters) || inputLetters.includes(targetLettersSorted) || targetLettersSorted === inputLetters) {{
                        lettersMatch = true;
                    }} else {{
                        // مطابقة تقريبية بالحروف الفردية
                        let matchCount = 0;
                        for (let char of inputLetters) {{
                            if (p.letters.includes(char)) matchCount++;
                        }}
                        if (matchCount >= Math.min(2, p.letters.length)) {{
                            lettersMatch = true;
                        }}
                    }}
                }}

                // مطابقة الأرقام حصرياً بعد الترتيب (تتجاوز تماماً مشكلة تبديل الخانات مثل 4674 و 4764)
                if (inputDigits && p.digits) {{
                    let targetDigitsSorted = p.digits.split('').sort().join('');
                    if (inputDigits === targetDigitsSorted || p.digits.includes(inputDigits) || inputDigits.includes(targetDigitsSorted)) {{
                        digitsMatch = true;
                    }}
                }}

                if (lettersMatch && digitsMatch) {{
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
