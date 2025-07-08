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
            st.session_state.page = "home"
            st.session_state.history = []
            st.session_state.edit_row = None
            st.session_state.close_row = None
            st.experimental_rerun()
    with col2:
        if st.button("🔙 Back"):
            if st.session_state.history:
                previous = st.session_state.history.pop()
                st.session_state.page = previous
            else:
                st.session_state.page = "home"
                st.session_state.history = []
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

def submit_request():
    st.markdown("<h2 style='color:#0073e6;'>📝 Submit Your Request</h2>", unsafe_allow_html=True)
    nav_buttons()
    with st.form("entry_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        target_resolution_date = st.date_input("Target Resolution Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            new_entry = pd.DataFrame([{
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Target Resolution Date": target_resolution_date,
                "Closing Comment": "",
                "Closed By": "",
                "Actual Resolution Date": ""
            }])
            new_entry.to_csv(CSV_FILE, mode='a', header=False, index=False)
            st.success("✅ Entry submitted successfully!")

def safe_to_date(val):
    if pd.isna(val) or val == "":
        return date.today()
    if isinstance(val, date):
        return val
    try:
        dt = pd.to_datetime(val)
        return dt.date()
    except Exception:
        return date.today()

def open_topics():
    st.markdown("<h2 style='color:#0073e6;'>📌 Open Topics</h2>", unsafe_allow_html=True)
    nav_buttons()

    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if open_df.empty:
        st.info("No open topics available.")
        return

    st.markdown("### 🗂️ Topics Table")

    header = st.columns([3, 2, 2, 3, 1, 1])
    header[0].markdown("**Topic**")
    header[1].markdown("**Owner**")
    header[2].markdown("**Status**")
    header[3].markdown("**Target Date**")
    header[4].markdown("**Close**")
    header[5].markdown("**Edit**")

    clicked_close = None
    clicked_edit = None

    for i, row in open_df.iterrows():
        with st.container():
            style = "background-color: #e6f2ff; border: 1px solid #cce6ff; padding: 10px; margin-bottom: 5px;"
            st.markdown(f"<div style='{style}'>", unsafe_allow_html=True)

            cols = st.columns([3, 2, 2, 3, 1, 1])
            cols[0].markdown(row["Topic"])
            cols[1].markdown(row["Owner"])
            cols[2].markdown(row["Status"])
            cols[3].markdown(row["Target Resolution Date"])

            if cols[4].button("Close", key=f"close_btn_{i}"):
                clicked_close = i
            if cols[5].button("Edit", key=f"edit_btn_{i}"):
                clicked_edit = i

            if st.session_state.close_row == i:
                with st.form(f"close_form_{i}"):
                    st.markdown("**🔒 Provide Closing Details**")
                    comment = st.text_area("Closing Comment", key=f"comment_{i}")
                    closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
                    action = st.radio("Action", ["Confirm Close", "Cancel"], key=f"close_action_{i}")
                    submitted = st.form_submit_button("Submit")
                    if submitted:
                        if action == "Confirm Close":
                            df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                            df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                            df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                            df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                            save_data(df)
                            st.success(f"✅ '{row['Topic']}' marked as Closed.")
