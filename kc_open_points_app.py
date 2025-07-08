import streamlit as st
import pandas as pd
from datetime import date
import os

CSV_FILE = "kc_open_points.csv"
REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

# Load data from CSV or show error if missing
@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        st.error("CSV file not found.")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["row_id"] = range(len(df))  # Unique in-memory ID
    return df

def save_data(df):
    df.drop(columns=["row_id"], inplace=True, errors='ignore')  # Remove before saving
    df.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()

def open_topics():
    st.header("📌 Open Topics")
    df = load_data()
    df_open = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if df_open.empty:
        st.info("No open topics available.")
        return

    if "edit_row" not in st.session_state:
        st.session_state.edit_row = None
    if "close_row" not in st.session_state:
        st.session_state.close_row = None

    # Global CSS for blue background and table styling with sticky headers
    st.markdown(
        """
        <style>
        body {
            background-color: #cce4f7;
        }
        .table-wrapper {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ccc;
            font-family: Arial, sans-serif;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            table-layout: fixed;
        }
        thead th {
            position: sticky;
            top: 0;
            background-color: #1976D2;
            color: white;
            padding: 8px;
            border: 1px solid #ccc;
            z-index: 10;
            text-align: left;
        }
        tbody td {
            border: 1px solid #ccc;
            padding: 6px 8px;
            overflow-wrap: break-word;
        }
        tbody tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .btn {
            border: 1px solid #1976D2;
            background-color: white;
            color: #1976D2;
            padding: 4px 8px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 4px;
            transition: background-color 0.3s ease;
            width: 100%;
        }
        .btn:hover {
            background-color: #1976D2;
            color: white;
        }
        .btn-cell {
            text-align: center;
            width: 70px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Build the static HTML table for styling + sticky header
    table_html = """
    <div class="table-wrapper">
    <table>
        <thead>
            <tr>
                <th style="width:5%;">S.No</th>
                <th style="width:25%;">Topic</th>
                <th style="width:15%;">Owner</th>
                <th style="width:15%;">Status</th>
                <th style="width:15%;">Target Date</th>
                <th style="width:10%;">Close</th>
                <th style="width:10%;">Edit</th>
            </tr>
        </thead>
        <tbody>
    """

    for idx, row in df_open.iterrows():
        table_html += f"""
            <tr>
                <td>{idx + 1}</td>
                <td>{row['Topic']}</td>
                <td>{row['Owner']}</td>
                <td>{row['Status']}</td>
                <td>{row['Target Resolution Date']}</td>
                <td class="btn-cell">🔒</td>
                <td class="btn-cell">✏️</td>
            </tr>
        """

    table_html += """
        </tbody>
    </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)

    st.write("")  # spacer

    # Interactive buttons and forms in Streamlit columns for actual actions
    for idx, row in df_open.iterrows():
        row_id = row["row_id"]
        cols = st.columns([0.05, 0.25, 0.15, 0.15, 0.15, 0.1, 0.1])
        cols[0].write(idx + 1)
        cols[1].write(row["Topic"])
        cols[2].write(row["Owner"])
        cols[3].write(row["Status"])
        cols[4].write(row["Target Resolution Date"])

        if cols[5].button("🔒 Close", key=f"close_{row_id}"):
            st.session_state.close_row = row_id
            st.session_state.edit_row = None

        if cols[6].button("✏️ Edit", key=f"edit_{row_id}"):
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
                    st.experimental_rerun()

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
                        df.loc[df["row_id"] == row_id, "Topic"] = new_topic
                        df.loc[df["row_id"] == row_id, "Owner"] = new_owner
                        df.loc[df["row_id"] == row_id, "Status"] = new_status
                        df.loc[df["row_id"] == row_id, "Target Resolution Date"] = new_date
                        save_data(df)
                        st.success("✅ Changes saved.")
                    st.session_state.edit_row = None
                    st.experimental_rerun()

    csv = df_open.drop(columns=["row_id"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Open Topics", data=csv, file_name="open_topics.csv", mime="text/csv")

def submit_request():
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

def closed_topics():
    st.header("✅ Closed Topics")
    df = load_data()
    df_closed = df[df["Status"].str.lower() == "closed"]
    st.dataframe(df_closed.drop(columns=["row_id"]), use_container_width=True)
    csv = df_closed.drop(columns=["row_id"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Closed Topics", data=csv, file_name="closed_topics.csv", mime="text/csv")

# --- Main App ---
st.set_page_config("K-C Tracker", layout="wide")
page = st.sidebar.radio("Navigate", ["Home", "Submit Request", "Open Topics", "Closed Topics"])

if page == "Home":
    st.title("📘 KC Issue Tracker")
    st.markdown("Use the sidebar to navigate between pages.")
elif page == "Submit Request":
    submit_request()
elif page == "Open Topics":
    open_topics()
elif page == "Closed Topics":
    closed_topics()
