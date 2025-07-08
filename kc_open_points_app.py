import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# File paths
CSV_FILE = "kc_open_points.csv"
USER_FILE = "users.csv"
LOG_FILE = "edit_log.csv"

# Columns expected in the data file
REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

# -------------- Utility Functions ------------------

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        st.error(f"{CSV_FILE} not found.")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["row_id"] = range(len(df))  # unique in-memory ID for edits
    return df

def save_data(df):
    df.drop(columns=["row_id"], inplace=True, errors='ignore')
    df.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()

@st.cache_data
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        st.error(f"{USER_FILE} not found.")
        return pd.DataFrame(columns=["username", "password", "role"])

def log_edit(old_row, new_row, editor):
    changes = []
    for field in ["Topic", "Owner", "Status", "Target Resolution Date"]:
        old_val = str(old_row[field])
        new_val = str(new_row[field])
        if old_val != new_val:
            changes.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "edited_by": editor,
                "field_changed": field,
                "topic_before": old_val,
                "topic_after": new_val
            })
    if changes:
        df_log = pd.DataFrame(changes)
        if os.path.exists(LOG_FILE):
            df_log.to_csv(LOG_FILE, mode="a", header=False, index=False)
        else:
            df_log.to_csv(LOG_FILE, mode="w", header=True, index=False)

# ---------------- Login ------------------

def login():
    st.sidebar.title("🔐 Login")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""

    users_df = load_users()

    if not st.session_state.logged_in:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user_row = users_df[users_df["username"] == username]
            if not user_row.empty and user_row.iloc[0]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user_row.iloc[0]["role"]
                st.sidebar.success(f"✅ Welcome, {username}")
            else:
                st.sidebar.error("❌ Invalid username or password")
        st.stop()
    else:
        st.sidebar.info(f"👤 {st.session_state.username} ({st.session_state.role})")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

# ---------------- Pages ------------------

def submit_request():
    if st.session_state.role not in ["editor", "admin"]:
        st.warning("🚫 You don't have permission to submit requests.")
        return
    st.header("📝 Submit Request")
    with st.form("form_submit"):
        topic = st.text_input("Topic")
        owner = st.text_input("Owner")
        status = st.text_input("Status")
        target_date = st.date_input("Target Resolution Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            df = load_data()
            new_row = {
                "Topic": topic,
                "Owner": owner,
                "Status": status,
                "Target Resolution Date": target_date,
                "Closing Comment": "",
                "Closed By": "",
                "Actual Resolution Date": ""
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("✅ Request submitted successfully!")

def open_topics():
    st.header("📌 Open Topics")
    df = load_data()
    df_open = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if "edit_row" not in st.session_state:
        st.session_state.edit_row = None
    if "close_row" not in st.session_state:
        st.session_state.close_row = None

    for _, row in df_open.iterrows():
        row_id = row["row_id"]
        st.markdown("---")
        cols = st.columns([3, 2, 2, 3, 1, 1])
        cols[0].markdown(f"**{row['Topic']}**")
        cols[1].markdown(row["Owner"])
        cols[2].markdown(row["Status"])
        cols[3].markdown(str(row["Target Resolution Date"]))

        # Show buttons only for editors/admins
        can_edit = st.session_state.role in ["editor", "admin"]

        if can_edit and cols[4].button("Close", key=f"close_{row_id}"):
            st.session_state.close_row = row_id
            st.session_state.edit_row = None

        if can_edit and cols[5].button("Edit", key=f"edit_{row_id}"):
            st.session_state.edit_row = row_id
            st.session_state.close_row = None

        if st.session_state.close_row == row_id:
            with st.form(f"close_form_{row_id}"):
                comment = st.text_area("Closing Comment", key=f"cmt_{row_id}")
                closed_by = st.text_input("Closed By", key=f"cby_{row_id}")
                action = st.radio("Action", ["Confirm Close", "Cancel"], key=f"close_act_{row_id}")
                submit = st.form_submit_button("Submit")
                if submit:
                    if action == "Confirm Close":
                        df.loc[df["row_id"] == row_id, "Status"] = "Closed"
                        df.loc[df["row_id"] == row_id, "Closing Comment"] = comment
                        df.loc[df["row_id"] == row_id, "Closed By"] = closed_by
                        df.loc[df["row_id"] == row_id, "Actual Resolution Date"] = date.today().isoformat()
                        save_data(df)
                        st.success("✅ Topic closed.")
                    st.session_state.close_row = None

        if st.session_state.edit_row == row_id:
            with st.form(f"edit_form_{row_id}"):
                new_topic = st.text_input("Topic", value=row["Topic"], key=f"et_{row_id}")
                new_owner = st.text_input("Owner", value=row["Owner"], key=f"eo_{row_id}")
                new_status = st.text_input("Status", value=row["Status"], key=f"es_{row_id}")
                new_date = st.date_input("Target Resolution Date", pd.to_datetime(row["Target Resolution Date"]), key=f"ed_{row_id}")
                action = st.radio("Action", ["Save Changes", "Cancel"], key=f"edit_act_{row_id}")
                submit = st.form_submit_button("Submit")
                if submit:
                    if action == "Save Changes":
                        old_row = row.copy()
                        new_data = {
                            "Topic": new_topic,
                            "Owner": new_owner,
                            "Status": new_status,
                            "Target Resolution Date": new_date
                        }
                        # Update dataframe
                        df.loc[df["row_id"] == row_id, "Topic"] = new_topic
                        df.loc[df["row_id"] == row_id, "Owner"] = new_owner
                        df.loc[df["row_id"] == row_id, "Status"] = new_status
                        df.loc[df["row_id"] == row_id, "Target Resolution Date"] = new_date
                        # Log the edit
                        log_edit(old_row, new_data, st.session_state.username)
                        save_data(df)
                        st.success("✅ Changes saved.")
                    st.session_state.edit_row = None

    csv = df_open.drop(columns=["row_id"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Open Topics", data=csv, file_name="open_topics.csv", mime="text/csv")

def closed_topics():
    st.header("✅ Closed Topics")
    df = load_data()
    df_closed = df[df["Status"].str.lower() == "closed"]
    st.dataframe(df_closed.drop(columns=["row_id"]), use_container_width=True)

    csv = df_closed.drop(columns=["row_id"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Closed Topics", data=csv, file_name="closed_topics.csv", mime="text/csv")

def view_edit_logs():
    if st.session_state.role != "admin":
        st.warning("🚫 Only admins can view the edit history.")
        return
    st.header("🛠️ Edit History Log")
    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)
        st.dataframe(logs, use_container_width=True)
        csv = logs.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Log", data=csv, file_name="edit_log.csv", mime="text/csv")
    else:
        st.info("No edits have been logged yet.")

# ----------------- Main -------------------

st.set_page_config("K-C Tracker", layout="wide")

login()

# Sidebar navigation based on role
if st.session_state.role == "admin":
    page = st.sidebar.radio("Go to", ["Home", "Submit Request", "Open Topics", "Closed Topics", "Edit Log"])
else:
    page = st.sidebar.radio("Go to", ["Home", "Submit Request", "Open Topics", "Closed Topics"])

if page == "Home":
    st.title("📘 KC Issue Tracker")
    st.markdown("Use the left sidebar to navigate between pages.")
elif page == "Submit Request":
    submit_request()
elif page == "Open Topics":
    open_topics()
elif page == "Closed Topics":
    closed_topics()
elif page == "Edit Log":
    view_edit_logs()
