import streamlit as st
import pandas as pd
from datetime import date
import os

CSV_FILE = "kc_open_points.csv"

REQUIRED_COLUMNS = [
    "Topic", "Owner", "Status", "Target Resolution Date",
    "Closing Comment", "Closed By", "Actual Resolution Date"
]

# Set blue background using CSS
page_bg_css = """
<style>
    .stApp {
        background-color: #cce6ff;
        color: #000000;
    }
    /* Style for bordered boxes for each row */
    .bordered-box {
        border: 2px solid #007acc;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        background-color: #e6f2ff;
    }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

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
    
    df["row_id"] = range(len(df))  # Create in-memory unique ID
    return df

def save_data(df):
    df.drop(columns=["row_id"], inplace=True, errors='ignore')  # Remove before saving
    df.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()

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
    df = load_data()
    df_open = df[df["Status"].str.lower() != "closed"].reset_index(drop=True)

    if df_open.empty:
        st.info("No open topics available.")
        return

    if "edit_row" not in st.session_state:
        st.session_state.edit_row = None
    if "close_row" not in st.session_state:
        st.session_state.close_row = None

    # Header row with borders using markdown inside columns
    header_cols = st.columns([1, 3, 2, 2, 3, 1, 1])
    header_cols[0].markdown("**S.No**")
    header_cols[1].markdown("**Topic**")
    header_cols[2].markdown("**Owner**")
    header_cols[3].markdown("**Status**")
    header_cols[4].markdown("**Target Date**")
    header_cols[5].markdown("**Close**")
    header_cols[6].markdown("**Edit**")

    for idx, row in df_open.iterrows():
        row_id = row["row_id"]
        # Put each row inside a container with bordered box style
        with st.container():
            st.markdown(f'<div class="bordered-box">', unsafe_allow_html=True)
            cols = st.columns([1, 3, 2, 2, 3, 1, 1])
            cols[0].write(idx + 1)  # Serial number starting from 1
            cols[1].write(row["Topic"])
            cols[2].write(row["Owner"])
            cols[3].write(row["Status"])
            cols[4].write(str(row["Target Resolution Date"]))

            if cols[5].button("Close", key=f"close_{row_id}"):
                st.session_state.close_row = row_id
                st.session_state.edit_row = None

            if cols[6].button("Edit", key=f"edit_{row_id}"):
                st.session_state.edit_row = row_id
                st.session_state.close_row = None

            st.markdown("</div>", unsafe_allow_html=True)

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
                try:
                    new_date = st.date_input("Target Resolution Date", pd.to_datetime(row["Target Resolution Date"]), key=f"ed_{row_id}")
                except:
                    new_date = st.date_input("Target Resolution Date", key=f"ed_{row_id}")
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

def closed_topics():
    st.header("✅ Closed Topics")
    df = load_data()
    df_closed = df[df["Status"].str.lower() == "closed"]
    st.dataframe(df_closed.drop(columns=["row_id"]), use_container_width=True)

    csv = df_closed.drop(columns=["row_id"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Closed Topics", data=csv, file_name="closed_topics.csv", mime="text/csv")

def home():
    st.title("📘 K-C Issue Tracker")
    st.write("Use the left sidebar to navigate between pages.")

def main():
    st.set_page_config("K-C Tracker", layout="wide")
    st.sidebar.title("📘 KC Tracker Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Submit Request", "Open Topics", "Closed Topics"])

    if page == "Home":
        home()
    elif page == "Submit Request":
        submit_request()
    elif page == "Open Topics":
        open_topics()
    elif page == "Closed Topics":
        closed_topics()

if __name__ == "__main__":
    main()
