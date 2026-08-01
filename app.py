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
    .mic-btn { font-size: 20px; padding: 12px 24px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; }
    .start-btn { background-color: #28a745; color: white; }
    .stop-btn { background-color: #dc3545; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ نظام الفحص والإملاء الفوري السريع")
st.markdown("---")

def normalize_text(text):
    if not text:
        return ""
    text = str(text).strip()
    
    # قاموس تحويل أسماء الحروف المنطوقة إلى أحرف مفردة
    letter_map = {
        'ألف': 'ا', 'الف': 'ا', 'باء': 'ب', 'با': 'ب', 'تاء': 'ت', 'تا': 'ت',
        'ثاء': 'ث', 'ثا': 'ث', 'جيم': 'ج', 'حاء': 'ح', 'حا': 'ح', 'خاء': 'خ', 'خا': 'خ',
        'دال': 'د', 'ذال': 'ذ', 'راء': 'ر', 'را': 'ر', 'زاي': 'ز', 'زين': 'ز', 'زا': 'ز',
        'سين': 'س', 'شين': 'ش', 'صاد': 'ص', 'ضاد': 'ض', 'طاء': 'ط', 'طا': 'ط',
        'ظاء': 'ظ', 'ظا': 'ظ', 'عين': 'ع', 'غين': 'غ', 'فاء': 'ف', 'فا': 'ف',
        'قاف': 'ق', 'كاف': 'ك', 'لام': 'ل', 'ميم': 'م', 'نون': 'ن', 'هاء': 'ه', 'ها': 'ه',
        'واو': 'و', 'ياء': 'ي', 'يا': 'ي'
    }
    
    # استبدال كلمات الحروف
    for word, letter in letter_map.items():
        text = re.sub(r'\b' + word + r'\b', letter, text)
        
    # تحويل الأرقام العربية الهندية (٠-٩) إلى أرقام إنجليزية (0-9)
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    translation_table = str.maketrans(arabic_digits, english_digits)
    text = text.translate(translation_table)
    
    # إزالة كل المسافات والرموز
    return re.sub(r'[^a-zA-Z0-9أ-ي]', '', text)

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)
    
    # تنظيف قوالب اللوحات في ملف الإكسيل بنفس المعيار
    raw_plates = df[column_name].dropna().tolist()
    normalized_map = {}
    
    for plate in raw_plates:
        norm_key = normalize_text(plate)
        if norm_key:
            normalized_map[norm_key] = str(plate)

    st.success(f"تم تحميل الملف! عدد اللوحات: {len(normalized_map)}")
    st.markdown("---")

    st.subheader("🎙️ الاستماع الفوري المستمر:")

    plates_keys = str(list(normalized_map.keys()))

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
        const existingPlatesKeys = new Set({plates_keys});
        let recognizing = false;
        let recognition;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            document.getElementById('status').innerText = "متصفحك لا يدعم التعرف الصوتي. استخدم Chrome على Android.";
        }} else {{
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'ar-SA';

            recognition.onstart = function() {{
                recognizing = true;
                document.getElementById('status').innerText = "🎙️ الميكروفون يعمل الآن.. انطق اللوحات مباشرة!";
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
                let currentTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {{
                    currentTranscript += event.results[i][0].transcript;
                }}

                if (currentTranscript.trim() !== '') {{
                    let rawText = currentTranscript.trim();
                    document.getElementById('liveText').innerText = rawText;
                    checkPlate(rawText);
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

        function normalizeJS(text) {{
            if (!text) return "";
            let t = text.trim();
            const letterMap = {{
                'ألف': 'ا', 'الف': 'ا', 'باء': 'ب', 'با': 'ب', 'تاء': 'ت', 'تا': 'ت',
                'ثاء': 'ث', 'ثا': 'ث', 'جيم': 'ج', 'حاء': 'ح', 'حا': 'ح', 'خاء': 'خ', 'خا': 'خ',
                'دال': 'د', 'ذال': 'ذ', 'راء': 'ر', 'را': 'ر', 'زاي': 'ز', 'زين': 'ز', 'زا': 'ز',
                'سين': 'س', 'شين': 'ش', 'صاد': 'ص', 'ضاد': 'ض', 'طاء': 'ط', 'طا': 'ط',
                'ظاء': 'ظ', 'ظا': 'ظ', 'عين': 'ع', 'غين': 'غ', 'فاء': 'ف', 'فا': 'ف',
                'قاف': 'ق', 'كاف': 'ك', 'لام': 'ل', 'ميم': 'م', 'نون': 'ن', 'هاء': 'ه', 'ها': 'ه',
                'واو': 'و', 'ياء': 'ي', 'يا': 'ي'
            }};

            for (let word in letterMap) {{
                let regex = new RegExp('\\\\b' + word + '\\\\b', 'g');
                t = t.replace(regex, letterMap[word]);
            }}

            t = t.replace(/[٠١٢٣٤٥٦٧٨٩]/g, function(d) {{
                return d.charCodeAt(0) - 1632;
            }});

            return t.replace(/[^a-zA-Z0-9أ-ي]/g, '');
        }}

        function checkPlate(fullText) {{
            let norm = normalizeJS(fullText);
            let resultBox = document.getElementById('resultBox');

            resultBox.style.display = 'block';

            if (existingPlatesKeys.has(norm)) {{
                resultBox.className = 'status-box found-box';
                resultBox.innerHTML = '⚠️ اللوحة موجودة في الملف!';
                
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
