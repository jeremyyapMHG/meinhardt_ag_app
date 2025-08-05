import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine
import re


def render(username):
    st.header("Analyze AG - Assessment View")

    devco_id = username.split("@")[0] if "@" in username else username

    with engine.begin() as conn:
        # Get all relevant inputs
        raw_submissions = pd.read_sql(
            text("""
                 SELECT data_point, field_name, value 
                 FROM devco_submissions 
                 WHERE devco_id = :devco_id
                 AND field_name = 'input_value'
                 """),
            conn,
            params={"devco_id": devco_id}
        )
        # Get assessment matrix
        matrix = pd.read_sql(text("SELECT * FROM assessment_matrix"), conn)

    if raw_submissions.empty:
        st.warning("No submissions found for this DevCo.")
        return

    st.subheader("=== CLEANED DEVCO INPUTS ===")

    flat_inputs = {}
    alias_map = {}

    for _, row in raw_submissions.iterrows():
        # Strip off any parentheses text from data_point (e.g., " (No.)", " (Text)", etc.)
        clean_point = re.sub(r"\s*\(.*?\)", "", row["data_point"]).strip()
        
        # Turn it into a valid Python identifier
        alias = re.sub(r"[^\w]", "_", clean_point).lower()
        alias_map[clean_point] = alias # for reference later
        
        # Parse numeric or fallback to zero
        try:
            flat_inputs[alias] = float(row["value"])
        except:
            flat_inputs[alias] = 0.0

    submissions_dict = dict(flat_inputs)

    results = [] 

    for _, row in matrix.iterrows():
        criteria = row["assessment_criteria"]
        formula = row["formula"]
        weight = row["weightage"]

        st.markdown(f"**Evaluating Formula for:** `{criteria}`")
        st.markdown(f"→ Raw formula: `{formula}`")

        # Step 1: Clean formula 
        cleaned = formula.replace("\xa0", " ")
        cleaned = re.sub(r"[“”]", '"', cleaned)
        cleaned = re.sub(r"[‘’]", "'", cleaned)
        cleaned_formula = re.sub(r"\s*\(.*?\)", "", cleaned)  # strip white space characters parentheses
        
        # Step 2: replace human-readable keys with aliases

        for clean_point, alias in alias_map.items():
            expr = cleaned_formula.replace(clean_point, alias)

        st.markdown(f"→ Replaced with values: `{expr}`")

        # Step 3: eval safely
        try:
            score = eval(expr, {}, submissions_dict)
            st.markdown(f"→ Computed score: `{score}`")

        except Exception as e:
            score = None
            st.markdown(f"→ Computed score: `{score}`")
            # error = str(e)

        results.append({
            "assessment_criteria": criteria,
            "score":               score,
            "weightage":           weight,
            # "error":               error,
            "formula":            cleaned
        })

    st.subheader("Final Computed Scores")
    st.dataframe(pd.DataFrame(results), use_container_width=True)
        # return pd.DataFrame(results)
    