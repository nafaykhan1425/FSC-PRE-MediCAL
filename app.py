"""
FSc Pre-Medical (KP) Textbook Library
Streamlit app for 1st Year & 2nd Year: Biology, Physics, Chemistry, English
"""

import base64
import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
BOOKS_JSON = BASE_DIR / "books.json"
MAX_EMBED_MB = 15  # local PDFs bigger than this are download-only (browser limits)

SUBJECT_ICONS = {
    "Biology": "🧬",
    "Physics": "⚛️",
    "Chemistry": "🧪",
    "English": "📖",
}

st.set_page_config(
    page_title="FSc Pre-Medical KP Books",
    page_icon="📚",
    layout="wide",
)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
@st.cache_data
def load_books() -> dict:
    with open(BOOKS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def drive_id(link: str) -> str | None:
    """Extract a Google Drive file id from a share link."""
    if not link:
        return None
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", link) or re.search(r"id=([a-zA-Z0-9_-]+)", link)
    return m.group(1) if m else None


def local_file(book: dict) -> Path | None:
    rel = book.get("file", "")
    if not rel:
        return None
    p = BASE_DIR / rel
    return p if p.exists() else None


def book_available(book: dict) -> bool:
    return bool(book.get("link")) or local_file(book) is not None


def show_pdf_from_bytes(data: bytes, height: int = 800) -> None:
    b64 = base64.b64encode(data).decode()
    html = (
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="{height}" style="border:none;"></iframe>'
    )
    components.html(html, height=height + 10, scrolling=True)


def show_pdf_from_link(link: str, height: int = 800) -> None:
    fid = drive_id(link)
    src = f"https://drive.google.com/file/d/{fid}/preview" if fid else link
    components.html(
        f'<iframe src="{src}" width="100%" height="{height}" '
        f'style="border:none;" allow="autoplay"></iframe>',
        height=height + 10,
    )


def download_link(book: dict) -> str | None:
    link = book.get("link", "")
    fid = drive_id(link)
    if fid:
        return f"https://drive.google.com/uc?export=download&id={fid}"
    return link or None


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
try:
    BOOKS = load_books()
except Exception as e:  # missing / broken json
    st.error(f"Could not read books.json: {e}")
    st.stop()

# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.title("📚 FSc Pre-Medical KP")
st.sidebar.caption("Khyber Pakhtunkhwa Textbook Library")

year = st.sidebar.radio("Select Year", list(BOOKS.keys()))
subject = st.sidebar.radio(
    "Select Subject",
    list(BOOKS[year].keys()),
    format_func=lambda s: f"{SUBJECT_ICONS.get(s, '📘')} {s}",
)

st.sidebar.divider()
view_mode = st.sidebar.radio("View", ["Read Book", "All Books Overview"])
st.sidebar.divider()
st.sidebar.info(
    "Books are for educational use. Please use only official / "
    "authorised copies of the KP Textbook Board books."
)

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
st.title("FSc Pre-Medical Textbooks (KP)")

if view_mode == "All Books Overview":
    st.subheader("All Books")
    for yr, subjects in BOOKS.items():
        st.markdown(f"### {yr}")
        cols = st.columns(len(subjects))
        for col, (subj, book) in zip(cols, subjects.items()):
            with col:
                with st.container(border=True):
                    st.markdown(f"#### {SUBJECT_ICONS.get(subj, '📘')} {subj}")
                    st.caption(book.get("title", ""))
                    if book_available(book):
                        st.success("Available")
                    else:
                        st.warning("Not added yet")
    st.stop()

# ---- Read Book view --------------------------------------------------------
book = BOOKS[year][subject]
st.subheader(f"{SUBJECT_ICONS.get(subject, '📘')} {subject} — {year}")
st.caption(book.get("title", ""))

if not book_available(book):
    st.warning(
        "This book has not been added yet. Put the PDF in the `books/` folder "
        "and/or add a Google Drive link in `books.json`, then redeploy."
    )
    st.stop()

path = local_file(book)
link = book.get("link", "")

tab_read, tab_dl, tab_info = st.tabs(["📖 Read", "⬇️ Download", "ℹ️ Details"])

with tab_read:
    height = st.slider("Viewer height", 500, 1200, 800, 50)
    if link:
        show_pdf_from_link(link, height)
    elif path:
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb <= MAX_EMBED_MB:
            show_pdf_from_bytes(path.read_bytes(), height)
        else:
            st.info(
                f"This PDF is {size_mb:.1f} MB — too large to preview here. "
                "Please use the Download tab."
            )

with tab_dl:
    if path:
        st.download_button(
            "⬇️ Download PDF",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/pdf",
        )
    dl = download_link(book)
    if dl:
        st.link_button("⬇️ Download from Google Drive", dl)

with tab_info:
    st.write(f"**Title:** {book.get('title', '-')}")
    st.write(f"**Year:** {year}")
    st.write(f"**Subject:** {subject}")
    if book.get("notes"):
        st.write(f"**Notes:** {book['notes']}")
    if path:
        st.write(f"**File size:** {path.stat().st_size / (1024 * 1024):.1f} MB")

st.divider()
st.caption("Made with Streamlit • FSc Pre-Medical • Khyber Pakhtunkhwa")
