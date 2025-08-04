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
        st.write(raw_submissions)
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
        raw_key     = f"{clean_point}"

        # Turn it into a valid Python identifier
        alias = re.sub(r"[^\w]", "_", raw_key).lower()
        alias_map[raw_key] = alias

        # Parse numeric or fallback to zero
        try:
            flat_inputs[alias] = float(row["value"])
        except:
            flat_inputs[alias] = 0.0
    local_vars = dict(flat_inputs)

    # Step A: Build alias map
    # alias_map = {}
    # for key in flat_inputs:
    #     alias = re.sub(r"[^\w]", "_", key.strip()).lower()
    #     alias_map[key] = alias
    
    # st.write("Alias Map: ", alias_map)

    # # Step B: Assign values to each alias variable
    # for original, alias in alias_map.items():
    #     try:
    #         exec(f"{alias} = float(flat_inputs[original])")
    #     except:
    #         exec(f"{alias} = 0")  # Default to 0 if conversion fails

    # st.write("Alias: ", alias)


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
        cleaned = re.sub(r"\s*\(.*?\)", "", cleaned)  # strip parentheses
        
        # Step 2: replace human-readable keys with aliases
        expr = cleaned

        for raw_key, alias in alias_map.items():
            expr = expr.replace(raw_key, alias)

        st.markdown(f"→ Replaced with values: `{expr}`")

        # Step 3: eval safely
        try:
            score = eval(expr, {}, local_vars)
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
    