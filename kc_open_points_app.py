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

# Apply styling to DataFrame
def style_table(df):
    return df.style.set_properties(**{
        'background-color': '#f9f9f9',
        'color': '#333',
        'border-color': 'gray'
    }).set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-weight', 'bold')]}
    ]).apply(lambda x: ['background-color: #f2f2f2' if i % 2 == 0 else '' for i in range(len(x))], axis=1)

# Streamlit app
st.set_page_config(page_title="K-C Tracker", layout="wide")
st.title("📊 K-C Tracker")

page = st.sidebar.selectbox("Navigate", ["Submit Request", "Open Topics", "Closed Topics"])
df = load_data()

if page == "Submit Request":
    st.header("📝 Submit Your Request")
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

elif page == "Open Topics":
    st.header("📌 Open Topics")
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if not open_df.empty:
        st.dataframe(style_table(open_df[["Topic", "Owner", "Status", "Target Resolution Date"]]), use_container_width=True)

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
    st.header("✅ Closed Topics")
    closed_df = df[df["Status"].str.lower() == "closed"]
    if not closed_df.empty:
        st.dataframe(style_table(closed_df[[
            "Topic", "Owner", "Target Resolution Date",
            "Actual Resolution Date", "Closed By", "Closing Comment"
        ]]), use_container_width=True)
    else:
        st.info("No closed topics available.")
