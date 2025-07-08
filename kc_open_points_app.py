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
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
        df.rename(columns={"Resolution Date": "Target Resolution Date"}, inplace=True)
        for col in ["Closing Comment", "Closed By", "Actual Resolution Date"]:
            if col not in df.columns:
                df[col] = ""
        df.to_csv(CSV_FILE, index=False)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS]

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "close_row" not in st.session_state:
    st.session_state.close_row = None
if "edit_row" not in st.session_state:
    st.session_state.edit_row = None

def nav_buttons():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home"):
            st.session_state.page = "home"
            st.session_state.close_row = None
            st.session_state.edit_row = None
            st.experimental_rerun()
    with col2:
        if st.button("🔙 Back"):
            st.session_state.page = "home"
            st.session_state.close_row = None
            st.session_state.edit_row = None
            st.experimental_rerun()

def home():
    st.title("📘 K-C Issue Tracker")
    st.write("Choose an option:")
    if st.button("📝 Submit Request"):
        st.session_state.page = "submit"
        st.experimental_rerun()
    if st.button("📌 Open Topics"):
        st.session_state.page = "open"
        st.experimental_rerun()
    if st.button("✅ Closed Topics"):
        st.session_state.page = "closed"
        st.experimental_rerun()

def submit_request():
    st.header("📝 Submit Request")
    nav_buttons()
    with st.form("submit_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        target_date = st.date_input("Target Resolution Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            df = load_data()
            new_entry = pd.DataFrame([{
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Target Resolution Date": target_date,
                "Closing Comment": "",
                "Closed By": "",
                "Actual Resolution Date": ""
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            save_data(df)
            st.success("✅ Entry submitted!")

def open_topics():
    st.header("📌 Open Topics")
    nav_buttons()
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if open_df.empty:
        st.info("No open topics.")
        return

    header_cols = st.columns([3,2,2,3,1,1])
    header_cols[0].markdown("**Topic**")
    header_cols[1].markdown("**Owner**")
    header_cols[2].markdown("**Status**")
    header_cols[3].markdown("**Target Date**")
    header_cols[4].markdown("**Close**")
    header_cols[5].markdown("**Edit**")

    for i, row in open_df.iterrows():
        cols = st.columns([3,2,2,3,1,1])
        cols[0].write(row["Topic"])
        cols[1].write(row["Owner"])
        cols[2].write(row["Status"])
        cols[3].write(row["Target Resolution Date"])

        if cols[4].button("Close", key=f"close_{i}"):
            st.session_state.close_row = i
            st.session_state.edit_row = None
            st.experimental_rerun()

        if cols[5].button("Edit", key=f"edit_{i}"):
            st.session_state.edit_row = i
            st.session_state.close_row = None
            st.experimental_rerun()

        # Close dialog
        if st.session_state.close_row == i:
            with st.form(f"close_form_{i}"):
                st.write(f"Close Topic: **{row['Topic']}**")
                comment = st.text_area("Closing Comment", key=f"close_comment_{i}")
                closed_by = st.text_input("Closed By", key=f"close_closed_by_{i}")
                action = st.radio("Action", ["Confirm Close", "Cancel"], key=f"close_action_{i}")
                submitted = st.form_submit_button("Submit")
                if submitted:
                    if action == "Confirm Close":
                        df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                        df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                        df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                        df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                        save_data(df)
                        st.success(f"✅ '{row['Topic']}' closed.")
                    st.session_state.close_row = None
                    st.experimental_rerun()

        # Edit dialog
        if st.session_state.edit_row == i:
            with st.form(f"edit_form_{i}"):
                st.write(f"Edit Topic: **{row['Topic']}**")
                new_topic = st.text_input("Topic", value=row["Topic"], key=f"edit_topic_{i}")
                new_owner = st.text_input("Owner", value=row["Owner"], key=f"edit_owner_{i}")
                new_status = st.text_input("Status", value=row["Status"], key=f"edit_status_{i}")
                try:
                    new_date = st.date_input("Target Resolution Date", value=pd.to_datetime(row["Target Resolution Date"]), key=f"edit_date_{i}")
                except:
                    new_date = st.date_input("Target Resolution Date", key=f"edit_date_{i}")
                action = st.radio("Action", ["Save Changes", "Cancel"], key=f"edit_action_{i}")
                submitted = st.form_submit_button("Submit")
                if submitted:
                    if action == "Save Changes":
                        df.loc[df["Topic"] == row["Topic"], "Topic"] = new_topic
                        df.loc[df["Topic"] == new_topic, "Owner"] = new_owner
                        df.loc[df["Topic"] == new_topic, "Status"] = new_status
                        df.loc[df["Topic"] == new_topic, "Target Resolution Date"] = new_date
                        save_data(df)
                        st.success(f"✅ '{new_topic}' updated.")
                    st.session_state.edit_row = None
                    st.experimental_rerun()

def closed_topics():
    st.header("✅ Closed Topics")
    nav_buttons()
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]
    if closed_df.empty:
        st.info("No closed topics.")
        return

    st.dataframe(closed_df[[
        "Topic", "Owner", "Target Resolution Date",
        "Actual Resolution Date", "Closed By", "Closing Comment"
    ]], use_container_width=True)

    csv = closed_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Closed Topics CSV",
        csv,
        file_name="closed_topics.csv",
        mime="text/csv"
    )

st.set_page_config(page_title="K-C Tracker", layout="wide")

if st.session_state.page == "home":
    home()
elif st.session_state.page == "submit":
    submit_request()
elif st.session_state.page == "open":
    open_topics()
elif st.session_state.page == "closed":
    closed_topics()
