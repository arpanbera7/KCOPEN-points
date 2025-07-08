import streamlit as st
import pandas as pd
from datetime import date
import os

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
        st.error("CSV file not found.")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    
    df["row_id"] = range(len(df))  # In-memory unique ID
    return df

def save_data(df):
    df.drop(columns=["row_id"], inplace=True, errors='ignore')  # Remove before saving
    df.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()

# Inject CSS once
def inject_css():
    st.markdown(
        """
        <style>
        /* Page background */
        .main {
            background-color: #cce4f7;
            padding: 10px 20px 30px 20px;
        }
        /* Table style */
        table {
            border-collapse: collapse;
            width: 100%;
        }
        thead th {
            position: sticky;
            top: 0;
            background-color: #005b96;
            color: white;
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            z-index: 100;
        }
        tbody td {
            border: 1px solid #ddd;
            padding: 8px;
        }
        tbody tr:nth-child(even) {
            background-color: #e6f0fa;
        }
        tbody tr:hover {
            background-color: #d0e2f5;
        }
        button {
            cursor: pointer;
            padding: 4px 8px;
            background-color: #0073e6;
            border: none;
            color: white;
            border-radius: 3px;
            font-size: 14px;
        }
        button:hover {
            background-color: #005bb5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

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

def open_topics():
    st.header("📌 Open Topics")
    inject_css()
    df = load_data()
    df_open = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if df_open.empty:
        st.info("No open topics available.")
        return

    if "edit_row" not in st.session_state:
        st.session_state.edit_row = None
    if "close_row" not in st.session_state:
        st.session_state.close_row = None

    # Build the table header and body HTML manually for better styling and fixed header
    table_html = """
    <table>
    <thead>
    <tr>
        <th style="width:5%;">S.No.</th>
        <th style="width:25%;">Topic</th>
        <th style="width:15%;">Owner</th>
        <th style="width:10%;">Status</th>
        <th style="width:15%;">Target Resolution Date</th>
        <th style="width:10%;">Close</th>
        <th style="width:10%;">Edit</th>
    </tr>
    </thead>
    <tbody>
    """

    for idx, row in df_open.iterrows():
        row_id = row["row_id"]
        table_html += f"""
        <tr>
            <td>{idx + 1}</td>
            <td>{row['Topic']}</td>
            <td>{row['Owner']}</td>
            <td>{row['Status']}</td>
            <td>{row['Target Resolution Date']}</td>
            <td><form><button id="close_{row_id}">Close</button></form></td>
            <td><form><button id="edit_{row_id}">Edit</button></form></td>
        </tr>
        """
    table_html += "</tbody></table>"

    # Display the table
    st.markdown(table_html, unsafe_allow_html=True)

    # Now display Close and Edit forms below table if any row selected
    for idx, row in df_open.iterrows():
        row_id = row["row_id"]

        # Close dialog form
        if st.session_state.close_row == row_id:
            with st.form(f"close_form_{row_id}"):
                st.write(f"🔒 Close topic: **{row['Topic']}**")
                comment = st.text_area("Closing Comment", key=f"cmt_{row_id}")
                closed_by = st.text_input("Closed By", key=f"cby_{row_id}")
                action = st.radio("Action", ["Confirm Close", "Cancel"], key=f"close_act_{row_id}")
                submitted = st.form_submit_button("Submit")
                if submitted:
                    if action == "Confirm Close":
                        df.loc[df["row_id"] == row_id, "Status"] = "Closed"
                        df.loc[df["row_id"] == row_id, "Closing Comment"] = comment
                        df.loc[df["row_id"] == row_id, "Closed By"] = closed_by
                        df.loc[df["row_id"] == row_id, "Actual Resolution Date"] = date.today().isoformat()
                        save_data(df)
                        st.success("✅ Topic closed.")
                    st.session_state.close_row = None
                    st.experimental_rerun()

        # Edit dialog form
        if st.session_state.edit_row == row_id:
            with st.form(f"edit_form_{row_id}"):
                new_topic = st.text_input("Topic", value=row["Topic"], key=f"et_{row_id}")
                new_owner = st.text_input("Owner", value=row["Owner"], key=f"eo_{row_id}")
                new_status = st.text_input("Status", value=row["Status"], key=f"es_{row_id}")
                new_date = st.date_input("Target Resolution Date", pd.to_datetime(row["Target Resolution Date"]), key=f"ed_{row_id}")
                action = st.radio("Action", ["Save Changes", "Cancel"], key=f"edit_act_{row_id}")
                submitted = st.form_submit_button("Submit")
                if submitted:
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

def closed_topics():
    st.header("✅ Closed Topics")
    inject_css()
    df = load_data()
    df_closed = df[df["Status"].str.lower() == "closed"]

    if df_closed.empty:
        st.info("No closed topics available.")
        return

    # Use pandas styling for closed topics to keep simple
    st.dataframe(df_closed.drop(columns=["row_id"]), use_container_width=True)

    csv = df_closed.drop(columns=["row_id"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Closed Topics", data=csv, file_name="closed_topics.csv", mime="text/csv")

def main():
    st.set_page_config(page_title="K-C Tracker", layout="wide")
    st.sidebar.title("📘 KC Tracker Navigation")
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

if __name__ == "__main__":
    main()
