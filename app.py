import streamlit as st
import pandas as pd
import re
import json

st.set_page_config(page_title="نظام فحص اللوحات الذكي الفاخر", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        direction: rtl;
        text-align: right;
    }
    .main-title { 
        font-size: 30px; 
        font-weight: 800; 
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 25px;
        text-shadow: 0 2px 10px rgba(56, 189, 248, 0.2);
    }
    .status-box { 
        font-size: 22px; 
        font-weight: bold; 
        text-align: right; 
        padding: 22px; 
        border-radius: 16px; 
        margin-top: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        animation: fadeIn 0.4s ease-in-out;
    }
    .box-found { 
        background: rgba(22, 163, 74, 0.15); 
        border: 2px solid #22c55e; 
        color: #4ade80; 
    }
    .box-not-found { 
        background: rgba(220, 38, 38, 0.15); 
        border: 2px solid #ef4444; 
        color: #f87171; 
        text-align: center; 
    }
    .mic-btn { 
        font-size: 18px; 
        padding: 16px 28px; 
        border-radius: 12px; 
        border: none; 
        cursor: pointer; 
        font-weight: bold; 
        margin: 6px; 
        width: 48%; 
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .start-btn { background: linear-gradient(135deg, #16a34a, #15803d); color: white; }
    .start-btn:hover { background: linear-gradient(135deg, #22c55e, #16a34a); transform: translateY(-2px); }
    .stop-btn { background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; }
    .stop-btn:hover { background: linear-gradient(135deg, #ef4444, #dc2626); transform: translateY(-2px); }
    .clear-btn { background: linear-gradient(135deg, #475569, #334155); color: white; }
    .clear-btn:hover { background: linear-gradient(135deg, #64748b, #475569); transform: translateY(-2px); }
    
    .interpreted-box { 
        background: rgba(30, 41, 59, 0.7); 
        backdrop-filter: blur(10px);
        border: 1px solid rgba(56, 189, 248, 0.3); 
        padding: 16px; 
        border-radius: 12px; 
        margin-top: 15px; 
        color: #38bdf8; 
        font-size: 22px; 
        font-weight: bold; 
        direction: rtl; 
        text-align: right; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    .share-container {
        margin-top: 15px;
        display: flex;
        gap: 10px;
        justify-content: center;
        flex-wrap: wrap;
    }
    .share-btn {
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        color: white;
        font-size: 14px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: 0.3s;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .whatsapp-btn { background-color: #25d366; }
    .facebook-btn { background-color: #1877f2; }
    .general-share-btn { background-color: #8b5cf6; }
    .share-btn:hover { opacity: 0.9; transform: scale(1.05); }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✨ نظام فحص اللوحات الذكي والفاخر بالصوت 🚀</div>', unsafe_allow_html=True)
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

uploaded_file = st.file_uploader("📂 اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("📌 اختر عمود اللوحات:", df.columns)
    
    raw_plates = df[column_name].dropna().tolist()
    plate_database = []
    
    for plate in raw_plates:
        letters, digits = parse_plate(plate)
        if len(letters) >= 1 or len(digits) >= 1:
            plate_database.append({
                'original': str(plate).strip(),
                'letters': letters,
                'digits': digits
            })

    st.success(f"💎 تمت مسح وتهيئة قاعدة البيانات بنجاح ({len(plate_database)} لوحة صالحة)!")
    st.markdown("---")

    st.subheader("🎙️ محطة الفحص الصوتي الذكي:")
    st.write("اضغط على زر التشغيل وتحدث باللوحة بوضوح (يعمل بثبات تام في الخلفية حتى عند التنقل):")

    db_json = json.dumps(plate_database, ensure_ascii=False)

    components_code = """
    <div style="direction: rtl; text-align: center;">
        <div>
            <button id="toggleBtn" class="mic-btn start-btn" onclick="toggleSpeech()">🔴 تشغيل الاستماع</button>
            <button class="mic-btn clear-btn" onclick="clearText()">🗑️ مسح النتائج</button>
        </div>
        
        <div id="status" style="margin-top: 10px; color: #94a3b8; font-size: 15px; font-weight: bold;">الميكروفون متوقف</div>
        
        <div class="interpreted-box">
            <div style="font-size: 13px; color: #94a3b8; margin-bottom: 4px; text-align: right;">ما فهمه البرنامج من الصوت:</div>
            <div id="liveText" style="text-align: right;">-</div>
        </div>

        <div id="resultBox" style="display:none;" class="status-box">
            <div id="resultMessage"></div>
            <div class="share-container" id="shareButtonsContainer"></div>
        </div>
    </div>

    <script>
        const plateDB = __DB_JSON__;
        let recognizing = false;
        let recognition = null;
        let lastSpokenText = "";
        let userWantedActive = localStorage.getItem("mic_active") === "true";

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            document.getElementById('status').innerText = "متصفحك لا يدعم التعرف الصوتي.";
        } else {
            try {
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.maxAlternatives = 10;
                recognition.lang = 'ar-SA';

                recognition.onstart = function() {
                    recognizing = true;
                    document.getElementById('status').innerText = "🎙️ جاري الاستماع.. تحدث الآن بوضوح!";
                    let btn = document.getElementById('toggleBtn');
                    btn.innerText = "⏹️ إيقاف الاستماع";
                    btn.className = "mic-btn stop-btn";
                };

                recognition.onerror = function(event) {
                    console.log("Speech Error event: ", event.error);
                };

                recognition.onend = function() {
                    if (userWantedActive) {
                        try { recognition.start(); } catch(e) {}
                    } else {
                        recognizing = false;
                        document.getElementById('status').innerText = "الميكروفون متوقف";
                        let btn = document.getElementById('toggleBtn');
                        btn.innerText = "🔴 تشغيل الاستماع";
                        btn.className = "mic-btn start-btn";
                    }
                };

                recognition.onresult = function(event) {
                    let bestInterpreted = "";

                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        let res = event.results[i];
                        for (let altIndex = 0; altIndex < res.length; altIndex++) {
                            let transcript = res[altIndex].transcript;
                            if (transcript) {
                                if (!bestInterpreted) bestInterpreted = transcript;
                            }
                        }
                    }

                    if (bestInterpreted && bestInterpreted !== lastSpokenText) {
                        lastSpokenText = bestInterpreted;
                        let processed = normalizeAndExtract(bestInterpreted);
                        
                        document.getElementById('liveText').innerText = processed.letters + processed.digits;
                        checkAndDisplay(processed.letters, processed.digits);
                    }
                };

                if (userWantedActive) {
                    try { recognition.start(); } catch(e) {}
                }

            } catch(e) {}
        }

        function toggleSpeech() {
            if (!recognition) return;
            if (recognizing) {
                userWantedActive = false;
                localStorage.setItem("mic_active", "false");
                recognizing = false;
                try { recognition.stop(); } catch(e) {}
            } else {
                userWantedActive = true;
                localStorage.setItem("mic_active", "true");
                lastSpokenText = "";
                try { recognition.start(); } catch(e) {}
            }
        }

        function clearText() {
            document.getElementById('liveText').innerText = "-";
            document.getElementById('resultBox').style.display = 'none';
            lastSpokenText = "";
        }

        function normalizeAndExtract(text) {
            let t = text;
            t = t.replace(/[٠-٩]/g, function(d) { return "٠١٢٣٤٥٦٧٨٩".indexOf(d); });
            
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

            t = t.replace(/حسين|حسن|حسون|سين|سني/g, "س")
                 .replace(/رقية|رقبه|راء|رائيه/g, "ر")
                 .replace(/بهاء|باها|باء|بائيه/g, "ب")
                 .replace(/زين|زينة|زاي/g, "ز")
                 .replace(/شيماء|شيم|شين/g, "ش")
                 .replace(/صالح|صلح|صاد/g, "ص")
                 .replace(/محمد|محمده|ميم/g, "م")
                 .replace(/علي|علا|عين/g, "ع")
                 .replace(/خالد|خلد|خاء/g, "خ")
                 .replace(/ناصر|نصر|نون/g, "ن")
                 .replace(/تيسير|يسير|تاء/g, "ت")
                 .replace(/قاسم|قسم|قاف/g, "ق")
                 .replace(/الف|ألف/g, "أ")
                 .replace(/دال|دولة/g, "د")
                 .replace(/جيم|جمل/g, "ج")
                 .replace(/هاء|هوا/g, "ه")
                 .replace(/واو/g, "و")
                 .replace(/لام/g, "ل")
                 .replace(/طاس|طاء/g, "ط");

            let rawLetters = (t.match(/[\\u0600-\\u06FF]/g) || []).join("").replace(/\\s+/g, '');
            let letters = rawLetters.length > 3 ? rawLetters.substring(0, 3) : rawLetters;

            let digits = (t.match(/[0-9]/g) || []).join("");
            if (digits.length > 4) {
                digits = digits.substring(0, 4);
            }

            return { letters: letters, digits: digits };
        }

        function checkAndDisplay(inputLetters, inputDigits) {
            let resultBox = document.getElementById('resultBox');
            let resultMsg = document.getElementById('resultMessage');
            let shareContainer = document.getElementById('shareButtonsContainer');

            if (inputLetters.length < 2 || inputDigits.length < 2) {
                resultBox.style.display = 'none';
                return;
            }

            let matches = [];
            plateDB.forEach(function(p) {
                let lMatch = (p.letters === inputLetters || p.letters.includes(inputLetters) || inputLetters.includes(p.letters) || levenshtein(p.letters, inputLetters) <= 1);
                let dMatch = (p.digits === inputDigits || p.digits.includes(inputDigits) || inputDigits.includes(p.digits));

                if (lMatch && dMatch) {
                    matches.push(p.original);
                }
            });

            let uniqueMatches = [...new Set(matches)];
            let fullSpokenText = inputLetters + inputDigits;
            let shareText = encodeURIComponent("نتيجة فحص اللوحة الذكية: " + fullSpokenText);

            if (uniqueMatches.length > 0) {
                resultBox.className = "status-box box-found";
                resultMsg.innerHTML = "✅ موجودة: " + uniqueMatches.join(" - ");
                
                let waLink = "https://api.whatsapp.com/send?text=" + shareText;
                let fbLink = "https://www.facebook.com/sharer/sharer.php?u=&quote=" + shareText;

                shareContainer.innerHTML = `
                    <a href="` + waLink + `" target="_blank" class="share-btn whatsapp-btn">💬 واتساب</a>
                    <a href="` + fbLink + `" target="_blank" class="share-btn facebook-btn">📘 فيسبوك</a>
                    <button onclick="navigator.share({title: 'فحص اللوحة', text: 'نتيجة فحص اللوحة: ' + '` + fullSpokenText + `'})" class="share-btn general-share-btn">🔗 مشاركة عامة</button>
                `;

                resultBox.style.display = 'block';
                if ("vibrate" in navigator) { 
                    navigator.vibrate([400, 200, 400]); 
                }
            } else {
                resultBox.className = "status-box box-not-found";
                resultMsg.innerHTML = "❌ غير موجودة في الملف";
                shareContainer.innerHTML = "";
                resultBox.style.display = 'block';
            }
        }

        function levenshtein(a, b) {
            if(a.length === 0) return b.length;
            if(b.length === 0) return a.length;
            let matrix = [];
            let i, j;
            for(i = 0; i <= b.length; i++) { matrix[i] = [i]; }
            for(j = 0; j <= a.length; j++) { matrix[0][j] = j; }
            for(i = 1; i <= b.length; i++) {
                for(j = 1; j <= a.length; j++) {
                    if(b.charAt(i-1) == a.charAt(j-1)) {
                        matrix[i][j] = matrix[i-1][j-1];
                    } else {
                        matrix[i][j] = Math.min(matrix[i-1][j-1] + 1, Math.min(matrix[i][j-1] + 1, matrix[i-1][j] + 1));
                    }
                }
            }
            return matrix[b.length][a.length];
        }
    </script>
    """

    components_code = components_code.replace("__DB_JSON__", db_json)
    st.components.v1.html(components_code, height=520)
