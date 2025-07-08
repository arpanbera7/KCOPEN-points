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

# Load data from Excel or CSV
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

# Save updated data to CSV
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Streamlit app
st.set_page_config(page_title="KC Open Points Tracker", layout="wide")
page = st.sidebar.selectbox("Select Page", ["Submit Your Request", "Open Points", "Closed Topics"])

df = load_data()

if page == "Submit Your Request":
    st.title("📝 KC Open Points - Submit Your Request")
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

elif page == "Open Points":
    st.title("📌 KC Open Points - Open Topics")
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if not open_df.empty:
        st.markdown("### Open Points Table")
        header_cols = st.columns([3, 2, 2, 2, 2])
        header_cols[0].markdown("**Topic**")
        header_cols[1].markdown("**Owner**")
        header_cols[2].markdown("**Status**")
        header_cols[3].markdown("**Target Resolution Date**")
        header_cols[4].markdown("**Action**")

        for i, row in open_df.iterrows():
            cols = st.columns([3, 2, 2, 2, 2])
            cols[0].markdown(row["Topic"])
            cols[1].markdown(row["Owner"])
            cols[2].markdown(row["Status"])
            cols[3].markdown(str(row["Target Resolution Date"]))
            if cols[4].button("Close", key=f"close_{i}"):
                with st.form(f"close_form_{i}"):
                    closing_comment = st.text_area("Closing Comment", key=f"comment_{i}")
                    closed_by = st.text_input("Closed By", key=f"closedby_{i}")
                    submit_close = st.form_submit_button("Confirm Close")
                    if submit_close:
                        df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                        df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = closing_comment
                        df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                        df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                        save_data(df)
                        st.success(f"✅ '{row['Topic']}' marked as Closed.")
                        st.experimental_rerun()
    else:
        st.info("No open topics available.")

elif page == "Closed Topics":
    st.title("✅ KC Open Points - Closed Topics")
    closed_df = df[df["Status"].str.lower() == "closed"]
    if not closed_df.empty:
        st.dataframe(closed_df[[
            "Topic", "Owner", "Target Resolution Date",
            "Actual Resolution Date", "Closed By", "Closing Comment"
        ]], use_container_width=True)
    else:
        st.info("No closed topics available.")
