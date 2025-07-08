import streamlit as st
import pandas as pd
import os
from datetime import date

# File paths
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

def style_table(df):
    return df.style.set_properties(**{
        'background-color': '#f0f8ff',
        'color': '#003366',
        'border-color': '#cce6ff'
    }).set_table_styles([{
        'selector': 'thead th',
        'props': [('background-color', '#0073e6'), ('color', 'white'), ('font-weight', 'bold')]
    }])

if "page" not in st.session_state:
    st.session_state.page = "home"

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

def open_topics():
    st.markdown("<h2 style='color:#0073e6;'>📌 Open Topics</h2>", unsafe_allow_html=True)
    nav_buttons()
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if not open_df.empty:
        st.markdown("### 🗂️ Topics Table")
        header = st.columns([3, 2, 2, 3, 3])
        header[0].markdown("**Topic**")
        header[1].markdown("**Owner**")
        header[2].markdown("**Status**")
        header[3].markdown("**Target Date**")
        header[4].markdown("**Close Action**")

        for i, row in open_df.iterrows():
            cols = st.columns([3, 2, 2, 3, 3])
            cols[0].markdown(row["Topic"])
            cols[1].markdown(row["Owner"])
            cols[2].markdown(row["Status"])
            cols[3].markdown(row["Target Resolution Date"])
            with cols[4]:
                with st.form(f"close_form_{i}"):
                    comment = st.text_input("Comment", key=f"comment_{i}")
                    closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
                    if st.form_submit_button("Close"):
                        df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                        df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                        df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                        df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                        save_data(df)
                        st.success(f"✅ '{row['Topic']}' marked as Closed.")
                        st.rerun()

        # Download Open Topics
        csv = open_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Open Topics as CSV",
            data=csv,
            file_name='open_topics.csv',
            mime='text/csv'
        )
    else:
        st.info("No open topics available.")

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

        csv = closed_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Closed Topics as CSV",
            data=csv,
            file_name='closed_topics.csv',
            mime='text/csv'
        )
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
