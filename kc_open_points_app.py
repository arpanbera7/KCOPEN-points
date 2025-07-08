import streamlit as st
import pandas as pd
import os
from datetime import date

EXCEL_FILE = "KC Open Points.xlsx"
CSV_FILE = "kc_open_points.csv"
USER_FILE = "users.csv"

REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

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
    # Clear cache to reload fresh data next time
    if "data" in st.session_state:
        del st.session_state["data"]

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame([
            {"username": "admin", "password": "admin", "role": "admin"},
            {"username": "user", "password": "user", "role": "user"}
        ])

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
if "page" not in st.session_state:
    st.session_state.page = "home"
if "close_row" not in st.session_state:
    st.session_state.close_row = None
if "edit_row" not in st.session_state:
    st.session_state.edit_row = None

def login():
    st.sidebar.title("🔐 Login")
    users_df = load_users()

    if not st.session_state.logged_in:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_clicked = st.sidebar.button("Login")

        if login_clicked:
            user_row = users_df[users_df["username"] == username]
            if not user_row.empty and user_row.iloc[0]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user_row.iloc[0]["role"]
                st.experimental_rerun()
            else:
                st.sidebar.error("❌ Invalid username or password")

        st.stop()

    else:
        st.sidebar.success(f"👤 {st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.experimental_rerun()

def nav_buttons():
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🏠 Home"):
            st.session_state.page = "home"
            st.session_state.close_row = None
            st.session_state.edit_row = None
            st.experimental_rerun()
    with col2:
        if st.button("🔙 Back"):
            # Go back to home from other pages
            if st.session_state.page in ["open", "closed", "submit"]:
                st.session_state.page = "home"
                st.session_state.close_row = None
                st.session_state.edit_row = None
                st.experimental_rerun()

def home():
    st.title("📘 K-C Issue Tracker")
    st.write("Welcome! Please choose an option below:")
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
    st.header("📝 Submit Your Request")
    nav_buttons()
    with st.form("entry_form"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        target_resolution_date = st.date_input("Target Resolution Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            df = load_data()
            new_entry = pd.DataFrame([{
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Target Resolution Date": target_resolution_date,
                "Closing Comment": "",
                "Closed By": "",
                "Actual Resolution Date": ""
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            save_data(df)
            st.success("✅ Entry submitted successfully!")

def open_topics():
    st.header("📌 Open Topics")
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

    for i, row in open_df.iterrows():
        cols = st.columns([3, 2, 2, 3, 1, 1])
        cols[0].write(row["Topic"])
        cols[1].write(row["Owner"])
        cols[2].write(row["Status"])
        cols[3].write(row["Target Resolution Date"])

        if cols[4].button("Close", key=f"close_btn_{i}"):
            st.session_state.close_row = i
            st.session_state.edit_row = None
            st.experimental_rerun()

        if cols[5].button("Edit", key=f"edit_btn_{i}"):
            st.session_state.edit_row = i
            st.session_state.close_row = None
            st.experimental_rerun()

    if st.session_state.close_row is not None:
        i = st.session_state.close_row
        row = open_df.iloc[i]
        with st.form(f"close_form_{i}"):
            st.write(f"🔒 Close topic: **{row['Topic']}**")
            comment = st.text_area("Closing Comment", key=f"comment_{i}")
            closed_by = st.text_input("Closed By", key=f"closed_by_{i}")
            submitted = st.form_submit_button("Submit")
            cancel = st.form_submit_button("Cancel")

            if submitted:
                df.loc[df["Topic"] == row["Topic"], "Status"] = "Closed"
                df.loc[df["Topic"] == row["Topic"], "Closing Comment"] = comment
                df.loc[df["Topic"] == row["Topic"], "Closed By"] = closed_by
                df.loc[df["Topic"] == row["Topic"], "Actual Resolution Date"] = date.today().isoformat()
                save_data(df)
                st.success(f"✅ '{row['Topic']}' marked as Closed.")
                st.session_state.close_row = None
                st.experimental_rerun()
            elif cancel:
                st.session_state.close_row = None
                st.experimental_rerun()

    if st.session_state.edit_row is not None:
        i = st.session_state.edit_row
        row = open_df.iloc[i]
        with st.form(f"edit_form_{i}"):
            st.write(f"✏️ Edit topic: **{row['Topic']}**")
            new_topic = st.text_input("Topic", value=row["Topic"], key=f"edit_topic_{i}")
            new_owner = st.text_input("Owner", value=row["Owner"], key=f"edit_owner_{i}")
            new_status = st.text_input("Status", value=row["Status"], key=f"edit_status_{i}")
            new_date = st.date_input("Target Resolution Date", value=pd.to_datetime(row["Target Resolution Date"]), key=f"edit_date_{i}")

            submitted = st.form_submit_button("Save Changes")
            cancel = st.form_submit_button("Cancel")

            if submitted:
                df.loc[df["Topic"] == row["Topic"], "Topic"] = new_topic
                df.loc[df["Topic"] == new_topic, "Owner"] = new_owner
                df.loc[df["Topic"] == new_topic, "Status"] = new_status
                df.loc[df["Topic"] == new_topic, "Target Resolution Date"] = new_date
                save_data(df)
                st.success(f"✅ '{new_topic}' updated successfully.")
                st.session_state.edit_row = None
                st.experimental_rerun()
            elif cancel:
                st.session_state.edit_row = None
                st.experimental_rerun()

    csv = open_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Open Topics as CSV",
        data=csv,
        file_name='open_topics.csv',
        mime='text/csv'
    )

def closed_topics():
    st.header("✅ Closed Topics")
    nav_buttons()
    df = load_data()
    closed_df = df[df["Status"].str.lower() == "closed"]
    if closed_df.empty:
        st.info("No closed topics available.")
        return
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

# --- Main ---
st.set_page_config(page_title="K-C Tracker", layout="wide")

login()  # must login first

if st.session_state.page == "home":
    home()
elif st.session_state.page == "submit":
    submit_request()
elif st.session_state.page == "open":
    open_topics()
elif st.session_state.page == "closed":
    closed_topics()
