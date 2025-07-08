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
    st.markdown("## 📘 K-C Issue Tracker\n", unsafe_allow_html=True)
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
    st.markdown("### 📝 Submit Your Request\n", unsafe_allow_html=True)
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
    st.markdown("### 📌 Open Topics\n", unsafe_allow_html=True)
    nav_buttons()
    df = load_data()
    open_df = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if not open_df.empty:
        st.markdown("### 🗂️ Topics Table")
        header = st.columns([3, 2, 2, 3, 1, 1])
        header[0].markdown("**Topic**")
        header[1].markdown("**Owner**")
        header[2].markdown("**Status**")
        header[3].markdown("**Target Date**")
        header[4].markdown("**Close**")
        header[5].markdown("**Edit**")

        for i, row in open_df.iterrows():
            with st.container():
                cols = st.columns([3, 2, 2, 3, 1, 1])
                cols[0].markdown(row["Topic"])
                cols[1].markdown(row["Owner"])
                cols[2].markdown(row["Status"])
                cols[3].markdown(row["Target Resolution Date"])
                with cols[4]:
                    if st.button("Close", key=f"close_btn_{i}"):
                        st.session_state.close_row = i
                        st.session_state.edit_row = None
                        st.rerun()
                with cols[5]:
                    if st.button("Edit", key=f"edit_btn_{i}"):
                        st.session_state.edit_row = i
                        st.session_state.close_row = None
                        st.rerun()

                if st.session_state.close_row == i:
                    with st.form(f"close_form_{i}"):
                        st.markdown("**🔒 Provide Closing Details**")
                        comment = st.text_area("Closing Comment", key=f"comment_{i}")
                        closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
                        col_submit, col_cancel = st.columns([1, 1])
                        if st.form_submit_button("Confirm Close"):
                            df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                            df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                            df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                            df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                            save_data(df)
                            st.success(f"✅ '{row['Topic']}' marked as Closed.")
                            st.session_state.close_row = None
                            st.rerun()
                        if st.form_submit_button("Cancel"):
                            st.session_state.close_row = None
                            st.rerun()

                if st.session_state.edit_row == i:
                    with st.form(f"edit_form_{i}"):
                        st.markdown("**✏️ Edit Topic Details**")
                        new_topic = st.text_input("Topic", value=row["Topic"], key=f"edit_topic_{i}")
                        new_owner = st.text_input("Owner", value=row["Owner"], key=f"edit_owner_{i}")
                        new_status = st.text_input("Status", value=row["Status"], key=f"edit_status_{i}")
                        new_date = st.date_input("Target Resolution Date", value=pd.to_datetime(row["Target Resolution Date"]), key=f"edit_date_{i}")
                        submitted = st.form_submit_button("Save Changes")
                        cancelled = st.form_submit_button("Cancel")
                        if submitted:
                            df.loc[df["Topic"] == row["Topic"], "Topic"] = new_topic
                            df.loc[df["Topic"] == new_topic, "Owner"] = new_owner
                            df.loc[df["Topic"] == new_topic, "Status"] = new_status
                            df.loc[df["Topic"] == new_topic, "Target Resolution Date"] = new_date
                            save_data(df)
                            st.success(f"✅ '{new_topic}' updated successfully.")
                            st.session_state.edit_row = None
                            st.rerun()
                        if cancelled:
                            st.session_state.edit_row = None
                            st.rerun()

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
    st.markdown("### ✅ Closed Topics\n", unsafe_allow_html=True)
    nav_buttons()
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]
    if not closed_df.empty:
        st.dataframe(closed_df[[
            "Topic", "Owner", "Target Resolution Date",
            "Actual Resolution Date", "Closed By", "Closing Comment"
        ]], use_container_width=True)
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
