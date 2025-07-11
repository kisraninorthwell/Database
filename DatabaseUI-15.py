#!/usr/bin/env python
# coding: utf-8

# In[2]:


import streamlit as st
import pandas as pd

# ---------- CONFIGURE PAGE ---------- #
st.set_page_config(
    page_title="Data Access Room",
    layout="wide",
    initial_sidebar_state="auto"
)

# ---------- CUSTOM CSS ---------- #
st.markdown("""
    <style>
        body {
            background-color: #f5f9ff;
        }
        .stApp {
            font-family: "Segoe UI", sans-serif;
        }
        h1 {
            color: #154c79;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #154c79;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .result-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.05);
        }
        .button-link {
            background-color: #0072b5;
            color: white !important;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- LOAD DATA ---------- #
csv_file = "Neurogram_Chat_With_GCS_Folder.csv"
try:
    df = pd.read_csv(csv_file)
except FileNotFoundError:
    st.error("CSV file not found. Please upload or place the file in the working directory.")
    st.stop()

df["Date Recorded"] = pd.to_datetime(df["Date Recorded"], errors="coerce")
hide_cols = ["Id", "Start time", "Completion time", "Email", "Name"]
gcs_cols = [col for col in df.columns if "GCS Folder" in col]
if not gcs_cols:
    st.error("No GCS Folder column found.")
    st.stop()
gcs_col = gcs_cols[0]

if "df" not in st.session_state:
    st.session_state.df = df.copy()

# ---------- HEADER ---------- #
st.markdown("""
    <h1 style='text-align: center;'>Data Access Room</h1>
""", unsafe_allow_html=True)

# ---------- PAGE NAVIGATION ---------- #
page = st.selectbox("Choose a Section", ["Neurogram Finder", "Central Database", "Add New Recording", "Functional Data"])

# ---------- PAGE: FINDER ---------- #
if page == "Neurogram Finder":
    st.markdown("<div class='section-title'>Search Criteria</div>", unsafe_allow_html=True)
    df = st.session_state.df

    mediator = st.selectbox("1. Select Mediator", sorted(df["Mediator"].dropna().unique()))
    filtered = df[df["Mediator"] == mediator]

    responder = st.radio("2. Responder Status", ["All", "Yes", "No"], horizontal=True)
    if responder != "All":
        filtered = filtered[filtered["Responder"].str.lower() == responder.lower()]

    methods = sorted(filtered["Administration Method"].dropna().unique())
    admin_method = st.selectbox("3. Administration Method", ["All"] + methods)
    if admin_method != "All":
        filtered = filtered[filtered["Administration Method"] == admin_method]

    gcs_option = st.radio("4. GCS Folder Link", ["All", "Yes", "No"], horizontal=True)
    has_link = filtered[gcs_col].notna()
    if gcs_option == "Yes":
        filtered = filtered[has_link]
    elif gcs_option == "No":
        filtered = filtered[~has_link]

    if not filtered["Date Recorded"].dropna().empty:
        start_date, end_date = st.date_input(
            "5. Date Range",
            [filtered["Date Recorded"].min(), filtered["Date Recorded"].max()]
        )
        filtered = filtered[
            (filtered["Date Recorded"] >= pd.to_datetime(start_date)) &
            (filtered["Date Recorded"] <= pd.to_datetime(end_date))
        ]

    st.markdown("---")
    st.markdown("### Matching Results")

    if filtered.empty:
        st.warning("No recordings found. Try adjusting the filters.")
    else:
        st.markdown(f"**Total Results:** {len(filtered)}")

        for idx, row in filtered.iterrows():
            title = row.get("Subject ID", f"Recording {idx+1}")
            with st.expander(title):
                for col in filtered.columns:
                    if col in hide_cols:
                        continue
                    val = row[col]
                    if pd.notna(val):
                        if col == gcs_col:
                            st.markdown(
                                f"<a href='{val}' target='_blank' class='button-link'>Open Folder</a>",
                                unsafe_allow_html=True
                            )
                        elif isinstance(val, pd.Timestamp):
                            st.markdown(f"**{col.strip()}:** {val.strftime('%B %d, %Y')}")
                        else:
                            st.markdown(f"**{col.strip()}:** {val}")

# ---------- PAGE: DATABASE ---------- #
elif page == "Central Database":
    st.header("Central Database")
    df = st.session_state.df

    editable_df = st.data_editor(
        df.drop(columns=hide_cols, errors="ignore"),
        use_container_width=True,
        num_rows="dynamic",
        key="editable_table"
    )

    st.download_button(
        "Download Edited CSV",
        data=editable_df.to_csv(index=False),
        file_name="edited_neurogram_data.csv",
        mime="text/csv"
    )

    if st.button("Save Changes to File"):
        st.session_state.df = editable_df.copy()
        st.session_state.df.to_csv(csv_file, index=False)
        st.success("Changes saved to Neurogram_Chat_With_GCS_Folder.csv")

# ---------- PAGE: ADD RECORD ---------- #
elif page == "Add New Recording":
    st.header("Add New Recording")
    df = st.session_state.df
    inputs = {}

    for col in df.columns:
        if col in hide_cols:
            continue
        col_dtype = df[col].dtype
        key_input = f"input_{col}"

        if pd.api.types.is_datetime64_any_dtype(col_dtype):
            inputs[col] = st.date_input(f"{col}", key=key_input)
        elif pd.api.types.is_numeric_dtype(col_dtype):
            inputs[col] = st.number_input(f"{col}", value=0.0, format="%.5f", key=key_input)
        else:
            inputs[col] = st.text_input(f"{col}", value="", key=key_input)

    if st.button("Add Recording"):
        new_row = {}
        for col, val in inputs.items():
            if col == "Date Recorded" and isinstance(val, pd._libs.tslibs.timestamps.Timestamp):
                new_row[col] = pd.to_datetime(val)
            else:
                new_row[col] = val
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state.df = new_df
        st.session_state.df.to_csv(csv_file, index=False)
        st.success("New recording added and saved!")

# ---------- PAGE: FUNCTIONAL DATA ---------- #
elif page == "Functional Data":
    st.markdown("<div class='section-title'>Functional Data Search</div>", unsafe_allow_html=True)
    df = st.session_state.df  # You will replace this with your functional data CSV later

    # Placeholder filters - update keys and options once you provide CSV
    questions = sorted(df["Question"].dropna().unique()) if "Question" in df.columns else ["Q1", "Q2", "Q3"]
    question = st.selectbox("Select Question", ["All"] + questions)

    mediators = sorted(df["Mediator"].dropna().unique()) if "Mediator" in df.columns else ["Mediator1", "Mediator2"]
    mediator = st.selectbox("Select Mediator", ["All"] + mediators)

    success_opts = ["All", "Yes", "No"]
    success = st.selectbox("Success", success_opts)

    date_min = df["Date Recorded"].min() if "Date Recorded" in df.columns else None
    date_max = df["Date Recorded"].max() if "Date Recorded" in df.columns else None
    if date_min and date_max:
        start_date, end_date = st.date_input("Date Range", [date_min, date_max])
    else:
        start_date, end_date = None, None

    researchers = sorted(df["Researcher"].dropna().unique()) if "Researcher" in df.columns else ["Researcher A", "Researcher B"]
    researcher = st.selectbox("Researcher", ["All"] + researchers)

    # Filtering logic (placeholder)
    filtered = df.copy()
    if question != "All" and "Question" in filtered.columns:
        filtered = filtered[filtered["Question"] == question]
    if mediator != "All":
        filtered = filtered[filtered["Mediator"] == mediator]
    if success != "All" and "Success" in filtered.columns:
        filtered = filtered[filtered["Success"].str.lower() == success.lower()]
    if start_date and end_date and "Date Recorded" in filtered.columns:
        filtered = filtered[
            (filtered["Date Recorded"] >= pd.to_datetime(start_date)) &
            (filtered["Date Recorded"] <= pd.to_datetime(end_date))
        ]
    if researcher != "All" and "Researcher" in filtered.columns:
        filtered = filtered[filtered["Researcher"] == researcher]

    st.markdown("---")
    st.markdown("### Matching Results")

    if filtered.empty:
        st.warning("No functional data found. Try adjusting the filters.")
    else:
        st.markdown(f"**Total Results:** {len(filtered)}")
        for idx, row in filtered.iterrows():
            title = row.get("Subject ID", f"Record {idx+1}")
            with st.expander(title):
                for col in filtered.columns:
                    if col in hide_cols:
                        continue
                    val = row[col]
                    if pd.notna(val):
                        if isinstance(val, pd.Timestamp):
                            st.markdown(f"**{col.strip()}:** {val.strftime('%B %d, %Y')}")
                        else:
                            st.markdown(f"**{col.strip()}:** {val}")


# In[ ]:




