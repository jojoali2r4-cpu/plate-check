import streamlit as st
import pandas as pd
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="نظام فحص لوحات السيارات",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 نظام فحص لوحات السيارات")
st.write("ارفعي ملف اللوحات ثم ابدئي التسجيل الصوتي.")

# =========================
# رفع ملف Excel
# =========================

uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"]
)

plates = []

if uploaded_file is not None:
    try:
        df = pd.read_excel(
            uploaded_file,
            sheet_name="بيانات"
        )

        if "اللوحه" not in df.columns:
            st.error("لم يتم العثور على عمود «اللوحه» في الملف.")

        else:
            plates = (
                df["اللوحه"]
                .dropna()
                .astype(str)
                .str.replace(" ", "", regex=False)
                .tolist()
            )

            st.success(
                f"تم تحميل {len(plates)} لوحة بنجاح."
            )

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")


st.divider()


# =========================
# التسجيل الصوتي
# =========================

st.subheader("🎙️ التسجيل الصوتي")

audio = mic_recorder(
    start_prompt="🎙️ بدء التسجيل",
    stop_prompt="⏹️ إيقاف التسجيل",
    just_once=True,
    use_container_width=True,
    key="car_plate_recorder"
)


# =========================
# بعد انتهاء التسجيل
# =========================

if audio is not None:

    st.success("تم تسجيل الصوت بنجاح.")

    # نحفظ الصوت في الذاكرة فقط
    audio_bytes = audio["bytes"]

    # نحتفظ به لاستخدامه لاحقًا مع تحويل الكلام إلى نص
    st.session_state["recorded_audio"] = audio_bytes


st.divider()


# =========================
# نتائج المطابقة
# =========================

st.subheader("📋 اللوحات المتطابقة")

if "matches" not in st.session_state:
    st.session_state.matches = []

if st.session_state.matches:
    st.table(st.session_state.matches)

else:
    st.info("لا توجد مطابقات حتى الآن.")
