import streamlit as st
import pandas as pd
import os
from datetime import date

# CSV file name
CSV_FILE = "kc_open_points.csv"

# Required columns
REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Actual Resolution Date",
    "Closing Comment", "Closed By"
]

# Load data from CSV and ensure all required columns exist
@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[REQUIRED_COLUMNS]

# Save updated data to CSV
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Streamlit app setup
st.set_page_config(page_title="KC Open Points Tracker", layout="wide")
page = st.sidebar.selectbox("Select Page", ["Submit Your Request", "Open Points", "Closed Topics"])

if page == "Submit Your Request":
    st.title("📝 KC Open Points - Submit Your Request")

    with st.form("entry_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        actual_resolution_date = st.date_input("Planned Resolution Date", format="YYYY-MM-DD")

        submitted = st.form_submit_button("Submit")

        if submitted:
            new_entry = pd.DataFrame([{
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Actual Resolution Date": actual_resolution_date,
                "Closing Comment": "",
                "Closed By": ""
            }])
            if os.path.exists(CSV_FILE):
                new_entry.to_csv(CSV_FILE, mode='a', header=False, index=False)
            else:
                new_entry.to_csv(CSV_FILE, index=False)
            st.success("✅ Entry submitted successfully!")

elif page == "Open Points":
    st.title("📌 KC Open Points - Open Topics")
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if not open_df.empty:
        st.dataframe(open_df[["Topic", "Owner", "Status", "Actual Resolution Date"]], use_container_width=True)

        st.subheader("🔒 Close a Topic")
        selected_topic = st.selectbox("Select a topic to close", open_df["Topic"].tolist())

        with st.form("close_form"):
            closing_comment = st.text_area("Closing Comment")
            closed_by = st.text_input("Closed By")
            close_submit = st.form_submit_button("Mark as Closed")

            if close_submit:
                df.loc[df["Topic"] == selected_topic, "Status"] = "Closed"
                df.loc[df["Topic"] == selected_topic, "Closing Comment"] = closing_comment
                df.loc[df["Topic"] == selected_topic, "Closed By"] = closed_by
                df.loc[df["Topic"] == selected_topic, "Actual Resolution Date"] = date.today().isoformat()
                save_data(df)
                st.success(f"✅ '{selected_topic}' marked as Closed.")
                st.experimental_rerun()
    else:
        st.info("No open topics available.")

elif page == "Closed Topics":
    st.title("✅ KC Open Points - Closed Topics")
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]

    if not closed_df.empty:
        st.dataframe(closed_df[[
            "Topic", "Owner", "Actual Resolution Date",
            "Closed By", "Closing Comment"
        ]], use_container_width=True)
    else:
        st.info("No closed topics available.")
