import streamlit as st
import pandas as pd
import os
from datetime import date

EXCEL_FILE = "KC Open Points.xlsx"
CSV_FILE = "kc_open_points.csv"

REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.read_excel(EXCEL_FILE, sheet_name=0, engine="openpyxl")
        df.rename(columns={"Resolution Date": "Target Resolution Date"}, inplace=True)
        df["Closing Comment"] = ""
        df["Closed By"] = ""
        df["Actual Resolution Date"] = ""
        df.to_csv(CSV_FILE, index=False)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS]

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "history" not in st.session_state:
    st.session_state.history = []
if "close_row" not in st.session_state:
    st.session_state.close_row = None
if "edit_row" not in st.session_state:
    st.session_state.edit_row = None

def nav_buttons():
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🏠 Home"):
            if st.session_state.page != "home":
                st.session_state.history = []
                st.session_state.edit_row = None
                st.session_state.close_row = None
                st.session_state.page = "home"
                st.experimental_rerun()
    with col2:
        if st.button("🔙 Back"):
            if st.session_state.history:
                st.session_state.page = st.session_state.history.pop()
                st.session_state.edit_row = None
                st.session_state.close_row = None
                st.experimental_rerun()
            else:
                if st.session_state.page != "home":
                    st.session_state.page = "home"
                    st.session_state.edit_row = None
                    st.session_state.close_row = None
                    st.experimental_rerun()

def navigate_to(page):
    if st.session_state.page != page:
        if st.session_state.page != "home":
            st.session_state.history.append(st.session_state.page)
        st.session_state.edit_row = None
        st.session_state.close_row = None
        st.session_state.page = page
        st.experimental_rerun()

def home():
    st.markdown("<h1 style='color:#0073e6;'>📘 K-C Issue Tracker</h1>", unsafe_allow_html=True)
    st.markdown("Welcome! Please choose an option below:")
    if st.button("📝 Submit Request"):
        navigate_to("submit")
    if st.button("📌 Open Topics"):
        navigate_to("open")
    if st.button("✅ Closed Topics"):
        navigate_to("closed")

# (Rest of functions unchanged, use the code I provided earlier for submit_request, open_topics, closed_topics, safe_to_date etc.)

# For brevity, I won't repeat all here, but use the full code from previous message.

st.set_page_config(page_title="K-C Tracker", layout="wide")

if st.session_state.page == "home":
    home()
elif st.session_state.page == "submit":
    submit_request()
elif st.session_state.page == "open":
    open_topics()
elif st.session_state.page == "closed":
    closed_topics()
else:
    st.write("Page not found.")
