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
    st.cache_data.clear()  # Ensure fresh reload

def safe_to_date(val):
    try:
        return pd.to_datetime(val).date()
    except:
        return date.today()

def submit_request():
    st.header("📝 Submit Your Request")
    with st.form("entry_form"):
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
            st.success("✅ Request submitted successfully.")

def open_topics():
    st.header("📌 Open Topics")
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if open_df.empty:
        st.info("No open topics available.")
        return

    if "edit_row" not in st.session_state:
        st.session_state.edit_row = None
    if "close_row" not in st.session_state:
        st.session_state.close_row = None

    for i, row in open_df.iterrows():
        with st.container():
            st.markdown("---")
            cols = st.columns([3, 2, 2, 3, 1, 1])
            cols[0].markdown(f"**{row['Topic']}**")
            cols[1].markdown(row["Owner"])
            cols[2].markdown(row["Status"])
            cols[3].markdown(str(row["Target Resolution Date"]))

            if cols[4].button("Close", key=f"close_{i}"):
                st.session_state.close_row = i
                st.session_state.edit_row = None

            if cols[5].button("Edit", key=f"edit_{i}"):
                st.session_state.edit_row = i
                st.session_state.close_row = None

            # Close form
            if st.session_state.close_row == i:
                with st.form(f"close_form_{i}"):
                    st.write("🔒 Provide Closing Details")
                    comment = st.text_area("Closing Comment", key=f"cmt_{i}")
                    closed_by = st.text_input("Closed By", key=f"cby_{i}")
                    action = st.radio("Action", ["Confirm Close", "Cancel"], key=f"close_action_{i}")
                    submit_close = st.form_submit_button("Submit")
                    if submit_close:
                        if action == "Confirm Close":
                            df.at[i, "Status"] = "Closed"
                            df.at[i, "Closing Comment"] = comment
                            df.at[i, "Closed By"] = closed_by
                            df.at[i, "Actual Resolution Date"] = date.today()
                            save_data(df)
                            st.success("✅ Topic closed successfully.")
                        st.session_state.close_row = None

            # Edit form
            if st.session_state.edit_row == i:
                with st.form(f"edit_form_{i}"):
                    st.write("✏️ Edit Topic Details")
                    new_topic = st.text_input("Topic", value=row["Topic"], key=f"et_{i}")
                    new_owner = st.text_input("Owner", value=row["Owner"], key=f"eo_{i}")
                    new_status = st.text_input("Status", value=row["Status"], key=f"es_{i}")
                    new_date = st.date_input("Target Resolution Date", value=safe_to_date(row["Target Resolution Date"]), key=f"ed_{i}")
                    action = st.radio("Action", ["Save Changes", "Cancel"], key=f"edit_action_{i}")
                    submit_edit = st.form_submit_button("Submit")
                    if submit_edit:
                        if action == "Save Changes":
                            df.at[i, "Topic"] = new_topic
                            df.at[i, "Owner"] = new_owner
                            df.at[i, "Status"] = new_status
                            df.at[i, "Target Resolution Date"] = new_date
                            save_data(df)
                            st.success("✅ Changes saved.")
                        st.session_state.edit_row = None

    csv = open_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Open Topics", data=csv, file_name="open_topics.csv", mime="text/csv")

def closed_topics():
    st.header("✅ Closed Topics")
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]
    if closed_df.empty:
        st.info("No closed topics found.")
        return
    st.dataframe(closed_df)
    csv = closed_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Closed Topics", data=csv, file_name="closed_topics.csv", mime="text/csv")

# Page config and navigation
st.set_page_config("K-C Tracker", layout="wide")
st.sidebar.title("📘 KC Tracker Navigation")
page = st.sidebar.radio("Go to", ["Home", "Submit Request", "Open Topics", "Closed Topics"])

if page == "Home":
    st.title("📘 KC Open Points Tracker")
    st.markdown("Welcome to the Issue Tracking System. Please choose an option from the left sidebar.")
elif page == "Submit Request":
    submit_request()
elif page == "Open Topics":
    open_topics()
elif page == "Closed Topics":
    closed_topics()
