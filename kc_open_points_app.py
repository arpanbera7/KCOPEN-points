import streamlit as st
import pandas as pd
import os
from datetime import date

# File paths
EXCEL_FILE = "KC Open Points.xlsx"
CSV_FILE = "kc_open_points.csv"

# Required columns
REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

# Load data
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

# Save data
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Style table
def style_table(df):
    return df.style.set_properties(**{
        'background-color': '#f0f8ff',
        'color': '#003366',
        'border-color': '#cce6ff'
    }).set_table_styles([{
        'selector': 'thead th',
        'props': [('background-color', '#0073e6'), ('color', 'white'), ('font-weight', 'bold')]
    }])

# Navigation state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Navigation buttons
def nav_buttons():
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🏠 Home"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("🔙 Back"):
            st.session_state.page = "home"
            st.rerun()

# Home Page
def home():
    st.markdown("<h1 style='color:#0073e6;'>📘 K-C Issue Tracker</h1>", unsafe_allow_html=True)
    st.markdown("Welcome! Please choose an option below:")
    if st.button("📝 Submit Request"):
        st.session_state.page = "submit"
        st.rerun()
    if st.button("📌 Open Topics"):
        st.session_state.page = "open"
        st.rerun()
    if st.button("✅ Closed Topics"):
        st.session_state.page = "closed"
        st.rerun()

# Submit Request Page
def submit_request():
    st.markdown("<h2 style='color:#0073e6;'>📝 Submit Your Request</h2>", unsafe_allow_html=True)
    nav_buttons()
    with st.form("entry_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        target_resolution_date = st.date_input("Target Resolution Date", format="YYYY-MM-DD")
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

# Open Topics Page
def open_topics():
    st.markdown("<h2 style='color:#0073e6;'>📌 Open Topics</h2>", unsafe_allow_html=True)
    nav_buttons()
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if not open_df.empty:
        for i, row in open_df.iterrows():
            with st.expander(f"🔹 {row['Topic']}"):
                st.write(f"**Owner:** {row['Owner']}")
                st.write(f"**Status:** {row['Status']}")
                st.write(f"**Target Resolution Date:** {row['Target Resolution Date']}")
                with st.form(f"close_form_{i}"):
                    closing_comment = st.text_area("Closing Comment", key=f"comment_{i}")
                    closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
                    close_submit = st.form_submit_button("Mark as Closed")
                    if close_submit:
                        df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                        df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = closing_comment
                        df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                        df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                        save_data(df)
                        st.success(f"✅ '{row['Topic']}' marked as Closed.")
                        st.rerun()
    else:
        st.info("No open topics available.")

# Closed Topics Page
def closed_topics():
    st.markdown("<h2 style='color:#0073e6;'>✅ Closed Topics</h2>", unsafe_allow_html=True)
    nav_buttons()
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]
    if not closed_df.empty:
        st.dataframe(style_table(closed_df[[
            "Topic", "Owner", "Target Resolution Date",
            "Actual Resolution Date", "Closed By", "Closing Comment"
        ]]), use_container_width=True)
    else:
        st.info("No closed topics available.")

# Page routing
st.set_page_config(page_title="K-C Tracker", layout="wide")
if st.session_state.page == "home":
    home()
elif st.session_state.page == "submit":
    submit_request()
elif st.session_state.page == "open":
    open_topics()
elif st.session_state.page == "closed":
    closed_topics()
