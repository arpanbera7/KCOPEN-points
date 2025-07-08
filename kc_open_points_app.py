import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

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

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "home"

if "history" not in st.session_state:
    st.session_state.history = []

if "close_row" not in st.session_state:
    st.session_state.close_row = None

if "edit_row" not in st.session_state:
    st.session_state.edit_row = None

def navigate_to(page):
    # Add current page to history before navigating, unless it's home or same page
    if st.session_state.page != page:
        if st.session_state.page != "home":
            st.session_state.history.append(st.session_state.page)
        # Clear edit/close state when navigating away
        st.session_state.edit_row = None
        st.session_state.close_row = None
        st.session_state.page = page
        st.experimental_rerun()

def go_back():
    if st.session_state.history:
        previous = st.session_state.history.pop()
        # Clear edit/close on back navigation
        st.session_state.edit_row = None
        st.session_state.close_row = None
        st.session_state.page = previous
        st.experimental_rerun()
    else:
        # No history, go home
        go_home()

def go_home():
    st.session_state.page = "home"
    st.session_state.history = []
    st.session_state.edit_row = None
    st.session_state.close_row = None
    st.experimental_rerun()

def nav_buttons():
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🏠 Home"):
            go_home()
    with col2:
        if st.button("🔙 Back"):
            go_back()

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

def safe_to_date(date_val):
    if isinstance(date_val, (datetime, pd.Timestamp)):
        return date_val.date()
    if isinstance(date_val, date):
        return date_val
    try:
        dt = pd.to_datetime(date_val, errors='coerce')
        if pd.isna(dt):
            return date.today()
        else:
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

    button_clicked = None

    for i, row in open_df.iterrows():
        with st.container():
            row_style = "background-color: #e6f2ff; border: 1px solid #cce6ff; padding: 10px; margin-bottom: 5px;"
            st.markdown(f"<div style='{row_style}'>", unsafe_allow_html=True)

            cols = st.columns([3, 2, 2, 3, 1, 1])
            cols[0].markdown(row["Topic"])
            cols[1].markdown(row["Owner"])
            cols[2].markdown(row["Status"])
            cols[3].markdown(row["Target Resolution Date"])

            if cols[4].button("Close", key=f"close_btn_{i}"):
                button_clicked = ("close", i)
            if cols[5].button("Edit", key=f"edit_btn_{i}"):
                button_clicked = ("edit", i)

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
                        # Close or Cancel: clear close_row and refresh
                        st.session_state.close_row = None
                        st.experimental_rerun()

            if st.session_state.edit_row == i:
                with st.form(f"edit_form_{i}"):
                    st.markdown("**✏️ Edit Topic Details**")
                    new_topic = st.text_input("Topic", value=row["Topic"], key=f"edit_topic_{i}")
                    new_owner = st.text_input("Owner", value=row["Owner"], key=f"edit_owner_{i}")
                    new_status = st.text_input("Status", value=row["Status"], key=f"edit_status_{i}")
                    new_date = st.date_input(
                        "Target Resolution Date",
                        value=safe_to_date(row["Target Resolution Date"]),
                        key=f"edit_date_{i}"
                    )
                    action = st.radio("Action", ["Save Changes", "Cancel"], key=f"edit_action_{i}")
                    submitted = st.form_submit_button("Submit")

                    if submitted:
                        if action == "Save Changes":
                            df.loc[df["Topic"] == row["Topic"], "Topic"] = new_topic
                            df.loc[df["Topic"] == new_topic, "Owner"] = new_owner
                            df.loc[df["Topic"] == new_topic, "Status"] = new_status
                            df.loc[df["Topic"] == new_topic, "Target Resolution Date"] = new_date
                            save_data(df)
                            st.success(f"✅ '{new_topic}' updated successfully.")
                        # Save or Cancel: clear edit_row and refresh
                        st.session_state.edit_row = None
                        st.experimental_rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    if button_clicked:
        action, idx = button_clicked
        if action == "close":
            st.session_state.close_row = idx
            st.session_state.edit_row = None
        elif action == "edit":
            st.session_state.edit_row = idx
            st.session_state.close_row = None
        st.experimental_rerun()

    csv = open_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Open Topics as CSV",
        data=csv,
        file_name='open_topics.csv',
        mime='text/csv'
    )

def closed_topics():
    st.markdown("<h2 style='color:#0073e6;'>✅ Closed Topics</h2>", unsafe_allow_html=True)
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
