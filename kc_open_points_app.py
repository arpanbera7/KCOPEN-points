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

if "page" not in st.session_state:
    st.session_state.page = "home"
if "close_row" not in st.session_state:
    st.session_state.close_row = None
if "edit_row" not in st.session_state:
    st.session_state.edit_row = None

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
        st.markdown("""
            <style>
            .custom-table {
                background-color: #e6f2ff;
                border-collapse: collapse;
                width: 100%;
            }
            .custom-table th, .custom-table td {
                border: 1px solid #99ccff;
                padding: 8px;
                text-align: left;
            }
            .custom-table th {
                background-color: #0073e6;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### 🗂️ Topics Table")
        st.markdown("<table class='custom-table'><tr><th>Topic</th><th>Owner</th><th>Status</th><th>Target Date</th><th>Close</th><th>Edit</th></tr>", unsafe_allow_html=True)

        for i, row in open_df.iterrows():
            st.markdown("<tr>", unsafe_allow_html=True)
            st.markdown(f"<td>{row['Topic']}</td><td>{row['Owner']}</td><td>{row['Status']}</td><td>{row['Target Resolution Date']}</td>", unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Close", key=f"close_btn_{i}"):
                    st.session_state.close_row = i
                    st.session_state.edit_row = None
                    st.rerun()
            with col2:
                if st.button("Edit", key=f"edit_btn_{i}"):
                    st.session_state.edit_row = i
                    st.session_state.close_row = None
                    st.rerun()
            st.markdown("</tr>", unsafe_allow_html=True)

            # Close form
            if st.session_state.close_row == i:
                with st.form(f"close_form_{i}"):
                    st.markdown("**🔒 Provide Closing Details**")
                    comment = st.text_area("Closing Comment", key=f"comment_{i}")
                    closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
                    col_submit, col_cancel = st.columns([1, 1])
                    with col_submit:
                        if st.form_submit_button("Confirm Close"):
                            df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                            df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                            df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                            df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                            save_data(df)
                            st.success(f"✅ '{row['Topic']}' marked as Closed.")
                            st.session_state.close_row = None
                            st.rerun()
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            st.session_state.close_row = None
                            st.rerun()

            # Edit form
            if st.session_state.edit_row == i:
                with st.form(f"edit_form_{i}"):
                    st.markdown("**✏️ Edit Topic Details**")
                    new_topic = st.text_input("Topic", value=row["Topic"], key=f"edit_topic_{i}")
                    new_owner = st.text_input("Owner", value=row["Owner"], key=f"edit_owner_{i}")
                    new_status = st.text_input("Status", value=row["Status"], key=f"edit_status_{i}")
                    new_date = st.date_input("Target Resolution Date", value=pd.to_datetime(row["Target Resolution Date"]), key=f"edit_date_{i}")
                    col_save, col_cancel = st.columns([1, 1])
                    with col_save:
                        if st.form_submit_button("Save Changes"):
                            df.loc[df["Topic"] == row["Topic"], "Topic"] = new_topic
                            df.loc[df["Topic"] == new_topic, "Owner"] = new_owner
                            df.loc[df["Topic"] == new_topic, "Status"] = new_status
                            df.loc[df["Topic"] == new_topic, "Target Resolution Date"] = new_date
                            save_data(df)
                            st.success(f"✅ '{new_topic}' updated successfully.")
                            st.session_state.edit_row = None
                            st.rerun()
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            st.session_state.edit_row = None
                            st.rerun()

        st.markdown("</table>", unsafe_allow_html=True)

        # Download Open Topics
        csv = open_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️
