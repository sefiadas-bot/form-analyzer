import streamlit as st
import base64
import tempfile
import os
import subprocess
from google import genai
from google.genai import types

SYSTEM_PROMPT = """
אתה כלי עזר מקצועי לכלאניות תקשורת לכתיבת פסקאות סיכום ומטרות טיפול מתוך טפסי הערכה תפקודית של ילדים.

מערכת הצבעים בטופס:
- ירוק = מיומנות שנרכשה במלואה
- כתום או ורוד = מיומנות בתהליך רכישה, זהו המוקד המרכזי למטרות הטיפול
- אדום = מיומנות שאינה קיימת כלל

המשימה: קרא את הטופס וכתוב פסקת סיכום של כ-10 שורות ומטרות טיפול.

עקרונות הסיכום:
- פתיחה קצרה על הילד: גיל, מסגרת, רקע רלוונטי
- חלוקה לתחומים: תקשורת, הבנה, הבעה, דיבור, משחק
- ניסוח חיובי והתפתחותי: לא חלש ב... אלא נמצא בשלב...
- זיהוי פערים בין תחומים
- אינטגרציה של ממצאים, לא רשימה

עקרונות המטרות:
- נגזרות מהסעיפים הכתומים
- מדידות ואינטגרטיביות
- מסודרות לפי תחומים

כתוב בעברית מקצועית.
"""

st.set_page_config(page_title="טופס הערכה", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700&display=swap');

    .stSpinner {
        background-color: #e8f0fe;
        border-radius: 10px;
        padding: 20px;
    }

    .stSpinner p {
        color: #1a1a2e !important;
        font-family: 'Heebo', Arial, sans-serif;
        font-size: 16px;
        font-weight: 600;
    }

    .result-card {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', Arial, sans-serif;
        font-size: 16px;
        line-height: 2;
        background-color: #ffffff;
        border-radius: 12px;
        padding: 30px 35px;
        margin-top: 10px;
        border: 1px solid #e0e7ef;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        color: #1a1a2e;
        white-space: pre-wrap;
    }

    .section-title {
        font-family: 'Heebo', Arial, sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: #6b7280;
        letter-spacing: 1px;
        margin-bottom: 8px;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:right; font-family:Heebo,Arial; color:#1a1a2e;'>ניתוח טופס הערכה</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:right; font-family:Heebo,Arial; color:#6b7280;'>העלי טופס הערכה מלא וקבלי פסקת סיכום ומטרות טיפול.</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("העלי קובץ PDF או Word", type=["pdf", "docx"])

if uploaded_file and st.button("✦ נתחי את הטופס", use_container_width=True):
    with st.spinner("מנתחת את הטופס, אנא המתיני..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            if uploaded_file.name.endswith(".docx"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir="/tmp") as tmp_docx:
                    tmp_docx.write(uploaded_file.read())
                    tmp_docx_path = tmp_docx.name
                subprocess.run([
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", "/tmp", tmp_docx_path
                ], check=True)
                tmp_pdf_path = tmp_docx_path.replace(".docx", ".pdf")
                with open(tmp_pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(tmp_docx_path)
                os.unlink(tmp_pdf_path)
            else:
                pdf_bytes = uploaded_file.read()

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                    "קראי את הטופס. שימי לב לצבעים: ירוק=נרכש, כתום=בתהליך, אדום=לא קיים. כתבי סיכום ומטרות."
                ],
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )

            st.session_state["result"] = response.text

        except Exception as e:
            st.error(f"שגיאה: {e}")

if "result" in st.session_state:
    result = st.session_state["result"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">תוצאת הניתוח</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="result-card">{result}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">העתקה — סמני הכל עם Ctrl+A ואחר כך Ctrl+C</div>', unsafe_allow_html=True)
    st.text_area("", value=result, height=220, label_visibility="collapsed")
