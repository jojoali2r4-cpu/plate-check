import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="فحص اللوحات السريع", layout="wide")

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

st.title("⚡ نظام الفحص والإملاء الفوري السريع")
st.markdown("---")

def extract_digits_and_letters(text):
    if not text:
        return "", ""
    text = str(text).strip()
    
    letter_map = {
        'ألف': 'ا', 'الف': 'ا', 'باء': 'ب', 'با': 'ب', 'تاء': 'ت', 'تا': 'ت',
        'ثاء': 'ث', 'ثا': 'ث', 'جيم': 'ج', 'حاء': 'ح', 'حا': 'ح', 'خاء': 'خ', 'خا': 'خ',
        'دال': 'د', 'ذال': 'ذ', 'راء': 'ر', 'را': 'ر', 'زاي': 'ز', 'زين': 'ز', 'زا': 'ز',
        'سين': 'س', 'سا': 'س', 'شين': 'ش', 'شا': 'ش', 'صاد': 'ص', 'صا': 'ص',
        'ضاد': 'ض', 'ضا': 'ض', 'طاء': 'ط', 'طا': 'ط', 'ظاء': 'ظ', 'ظا': 'ظ',
        'عين': 'ع', 'غين': 'غ', 'فاء': 'ف', 'فا': 'ف', 'قاف': 'ق', 'قا': 'ق',
        'كاف': 'ك', 'كا': 'ك', 'لام': 'ل', 'لا': 'ل', 'ميم': 'م', 'نون': 'ن',
        'هاء': 'ه', 'ها': 'ه', 'واو': 'و', 'ياء': 'ي', 'يا': 'ي'
    }
    
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(arabic_digits, english_digits))
    
    words = text.split()
    converted_words = [letter_map.get(w, w) for w in words]
    clean_str = "".join(converted_words)
    
    letters = "".join(re.findall(r'[أ-يa-zA-Z]', clean_str))
    digits = "".join(re.findall(r'[0-9]', clean_str))
    
    return letters, digits

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)
    
    raw_plates = df[column_name].dropna().tolist()
    plate_database = []
    
    for plate in raw_plates:
        letters, digits = extract_digits_and_letters(plate)
        if letters or digits:
            plate_database.append({
                'original': str(plate),
                'letters': letters,
                'digits': digits
            })

    st.success(f"تم تحميل الملف بنجاح! عدد اللوحات: {len(plate_database)}")
    st.markdown("---")

    st.subheader("🎙️ الاستماع المباشر الفوري:")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = f"""
    <div style="direction: rtl; text-align: center; font-family: sans-serif;">
        <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 بدء الاستماع المستمر</button>
        <div id="status" style="margin-top: 10px; color: #888; font-size: 14px;">الميكروفون متوقف</div>
        
        <div style="margin-top: 20px;">
            <div style="font-size: 16px; color: #555;">الكلمة المنطوقة حالياً:</div>
            <div id="liveText" style="font-size: 26px; font-weight: bold; color: #007bff; min-height: 40px; margin: 10px 0;">-</div>
        </div>

        <div id="resultBox" class="status-box" style="display:none;"></div>
    </div>

    <script>
        const plateDB = {db_json};
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            document.getElementById('status').innerText = "المتصفح لا يدعم التحدث المباشر. استخدم Chrome على أندرويد.";
        }} else {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ الميكروفون يعمل.. انطق اللوحات طوالي!";
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
                let lastPhrase = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    lastPhrase = event.results[i][0].transcript;
                }}

                if (lastPhrase.trim() !== '') {{
                    document.getElementById('liveText').innerText = lastPhrase;
                    checkPlate(lastPhrase);
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

        function parseSpoken(text) {{
            if (!text) return {{ letters: "", digits: "" }};
            let letterMap = {{
                'ألف': 'ا', 'الف': 'ا', 'باء': 'ب', 'با': 'ب', 'تاء': 'ت', 'تا': 'ت',
                'ثاء': 'ث', 'ثا': 'ث', 'جيم': 'ج', 'حاء': 'ح', 'حا': 'ح', 'خاء': 'خ', 'خا': 'خ',
                'دال': 'د', 'ذال': 'ذ', 'راء': 'ر', 'را': 'ر', 'زاي': 'ز', 'زين': 'ز', 'زا': 'ز',
                'سين': 'س', 'سا': 'س', 'شين': 'ش', 'شا': 'ش', 'صاد': 'ص', 'صا': 'ص',
                'ضاد': 'ض', 'ضا': 'ض', 'طاء': 'ط', 'طا': 'ط', 'ظاء': 'ظ', 'ظا': 'ظ',
                'عين': 'ع', 'غين': 'غ', 'فاء': 'ف', 'فا': 'ف', 'قاف': 'ق', 'قا': 'ق',
                'كاف': 'ك', 'كا': 'ك', 'لام': 'ل', 'لا': 'ل', 'ميم': 'م', 'نون': 'ن',
                'هاء': 'ه', 'ها': 'ه', 'واو': 'و', 'ياء': 'ي', 'يا': 'ي'
            }};

            let t = text.replace(/[٠١٢٣٤٥٦٧٨٩]/g, function(d) {{ return d.charCodeAt(0) - 1632; }});
            let words = t.trim().split(/\\s+/);
            let converted = words.map(w => letterMap[w] || w).join("");

            let letters = (converted.match(/[أ-يa-zA-Z]/g) || []).join("");
            let digits = (converted.match(/[0-9]/g) || []).join("");

            return {{ letters, digits }};
        }}

        function checkPlate(phrase) {{
            let spoken = parseSpoken(phrase);
            let resultBox = document.getElementById('resultBox');
            resultBox.style.display = 'block';

            if (!spoken.digits && !spoken.letters) return;

            // مطابقة مرنة: مطابقة الأرقام + توفر الحروف
            let match = plateDB.find(p => {{
                if (spoken.digits && p.digits === spoken.digits) {{
                    if (!spoken.letters || p.letters.includes(spoken.letters) || spoken.letters.includes(p.letters)) {{
                        return true;
                    }}
                }}
                if (spoken.letters && p.letters === spoken.letters && spoken.digits === p.digits) {{
                    return true;
                }}
                return false;
            }});

            if (match) {{
                resultBox.className = 'status-box found-box';
                resultBox.innerHTML = '⚠️ اللوحة موجودة بالملف: (' + match.original + ')';
                
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
