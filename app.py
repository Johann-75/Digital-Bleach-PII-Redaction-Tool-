import streamlit as st
import fitz
import gc
from redactor import Redactor

MAX_FILE_MB = 20

st.set_page_config(
    page_title="Digital Bleach | Enterprise Document Security",
    layout="wide",
    page_icon="🔐"
)

@st.cache_resource
def initialize_nltk_data():
    Redactor.setup_nltk()

initialize_nltk_data()

def local_css():
    st.markdown("""
    <style>
        /* System font stack — no external network request */
        .stApp {
            background-color: #0F172A;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: #F8FAFC;
        }

        [data-testid="stSidebar"] { display: none; }

        .main-title {
            color: #FFFFFF;
            font-weight: 800;
            font-size: 2.8rem;
            letter-spacing: -0.03em;
            margin-bottom: 0.5rem;
        }
        .main-subtitle {
            color: #94A3B8;
            font-size: 1.1rem;
            margin-bottom: 2.5rem;
        }
        .section-header {
            color: #38B2AC;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
            display: block;
        }

        [data-testid="stFileUploader"] {
            background-color: #1E293B;
            border: 1px dashed #334155;
            border-radius: 16px;
            padding: 2rem;
        }
        [data-testid="stFileUploader"] section {
            background-color: #0F172A !important;
            border-radius: 12px;
            border: 1px solid #334155;
        }
        [data-testid="stFileUploader"] label { color: #E2E8F0 !important; font-weight: 500; }

        .stButton>button {
            background-color: #3B82F6;
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 1rem;
            padding: 0.8rem 2.5rem;
            transition: all 0.2s;
            box-shadow: 0 10px 15px -3px rgba(59,130,246,0.3);
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #2563EB;
            transform: translateY(-1px);
            color: white;
            border: none;
        }

        .page-nav {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        hr { border-top: 1px solid #334155; margin: 3rem 0; }
    </style>
    """, unsafe_allow_html=True)

local_css()

st.markdown('<h1 class="main-title">Digital Bleach</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Enterprise-Grade Document Scrubbing & PII Redaction</p>', unsafe_allow_html=True)

st.markdown('<span class="section-header">Upload Document</span>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Drop PDF here or click to browse",
    type=["pdf"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    # ── Session State Guard ──────────────────────────────────────────────
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        st.session_state.redacted_bytes = None
        st.session_state.total_pages = 0

    # ── File size guard ──────────────────────────────────────────────────
    file_bytes = uploaded_file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        st.error(f"File too large ({size_mb:.1f} MB). Please upload a PDF under {MAX_FILE_MB} MB.")
        st.stop()

    if st.session_state.redacted_bytes is None:
        with st.spinner("Analyzing and masking sensitive data..."):
            try:
                # ── Check for selectable text ────────────────────────────────────
                probe = fitz.open(stream=file_bytes, filetype="pdf")
                has_text = any(len(p.get_text().strip()) > 0 for p in probe)
                st.session_state.total_pages = len(probe)
                probe.close()

                if not has_text:
                    st.error("No selectable text detected. Please provide a text-based PDF, not a scanned image.")
                    st.stop()

                # ── Redact ───────────────────────────────────────────────────────
                redactor = Redactor(file_bytes)
                redactor.redact_all()
                st.session_state.redacted_bytes = redactor.save()
                redactor.doc.close()
            except Exception as e:
                st.error(f"Redaction engine failed: {e}")
                st.stop()

    total_pages = st.session_state.total_pages
    redacted_bytes = st.session_state.redacted_bytes

    # ── Page navigator ───────────────────────────────────────────────────
    st.markdown("---")
    if total_pages > 1:
        page_index = st.slider(
            f"Page (1 of {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            format="Page %d"
        ) - 1  # convert to 0-indexed
    else:
        page_index = 0

    # ── Side-by-side preview ─────────────────────────────────────────────
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<span class="section-header">Original Data Stream</span>', unsafe_allow_html=True)
        # Isolated reader for before-image — doesn't share state with redactor
        before_doc = fitz.open(stream=file_bytes, filetype="pdf")
        img_before = before_doc[page_index].get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes()
        before_doc.close()
        st.image(img_before, use_container_width=True)

    with col2:
        st.markdown('<span class="section-header">Secure Redacted Output</span>', unsafe_allow_html=True)
        after_doc = fitz.open(stream=redacted_bytes, filetype="pdf")
        img_after = after_doc[page_index].get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes()
        after_doc.close()
        st.image(img_after, use_container_width=True)

    # ── Download ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.success("Analysis complete: sensitive PII entities have been permanently masked.")

    st.download_button(
        label="Download Secure PDF",
        data=redacted_bytes,
        file_name=f"REDACTED_{uploaded_file.name}",
        mime="application/pdf",
        use_container_width=True,
    )

    # ── Memory Cleanup ──────────────────────────────────────────────────
    del file_bytes
    gc.collect()

else:
    st.markdown("---")
    st.info("Awaiting file upload to initiate automated redaction.")

# ── Dynamic Configuration Manager ───────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("🛠️ Advanced: System Configuration"):
    st.markdown('<span class="section-header">Rule Management Engine</span>', unsafe_allow_html=True)
    st.info("Modify global redaction patterns and stop-words. Changes are applied instantly to the engine.")
    
    try:
        with open("rules.json", "r") as f:
            current_rules = f.read()
        
        new_rules = st.text_area(
            "Rules Definition (JSON)",
            value=current_rules,
            height=400,
            help="Update PII patterns, non-PII labels, or prose keywords here."
        )
        
        if st.button("Update System Rules", type="secondary"):
            try:
                # Validate JSON before saving
                json_data = json.loads(new_rules)
                with open("rules.json", "w") as f:
                    json.dump(json_data, f, indent=2)
                st.success("Configuration updated successfully! The engine has been re-initialized.")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON structure: {e}")
            except Exception as e:
                st.error(f"Failed to save configuration: {e}")
                
    except Exception as e:
        st.error(f"Could not load configuration: {e}")