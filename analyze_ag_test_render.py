# import streamlit as st
# import pandas as pd
# from sqlalchemy import text
# from db import engine
# import re


# def render(username):
#     # st.header("Analyze AG - Assessment View")

#     devco_id = username.split("@")[0] if "@" in username else username

#     with engine.begin() as conn:
#         # Get all relevant inputs
#         raw_submissions = pd.read_sql(
#             text("SELECT data_point_id, field_name, value FROM devco_submissions WHERE devco_id = :devco_id"),
#             conn,
#             params={"devco_id": devco_id}
#         )
#         print(raw_submissions)
#         # Get assessment matrix
#         matrix = pd.read_sql(text("SELECT * FROM assessment_matrix"), conn)

#     if raw_submissions.empty:
#         print("No submissions found for this DevCo.")
#         return

#     # st.subheader("=== CLEANED DEVCO INPUTS ===")

#     flat_inputs = {}
#     for _, row in raw_submissions.iterrows():
#         field = row["field_name"]
#         val = row["value"]
#         try:
#             flat_inputs[field] = float(val)
#         except:
#             flat_inputs[field] = val

#     print(flat_inputs)

#     # Step A: Build alias map
#     alias_map = {}
#     for key in flat_inputs:
#         alias = re.sub(r"[^\w]", "_", key.strip()).lower()
#         alias_map[key] = alias
    
#     print("Alias Map: ", alias_map)

#     # Step B: Assign values to each alias variable
#     for original, alias in alias_map.items():
#         try:
#             exec(f"{alias} = float(flat_inputs[original])")
#         except:
#             exec(f"{alias} = 0")  # Default to 0 if conversion fails

#     print("Alias: ", alias)

#     import re

#     results = [] 

#     for _, row in matrix.iterrows():
#         criteria = row["assessment_criteria"]
#         formula = row["formula"]
#         weight = row["weightage"]

#         print(f"**Evaluating Formula for:** `{criteria}`")
#         print(f"→ Raw formula: `{formula}`")

#         try:
#             # STEP 1: Clean formula (remove non-breaking spaces, smart quotes, etc.)
#             cleaned_formula = formula.replace('\xa0', ' ')  # U+00A0 non-breaking space
#             cleaned_formula = re.sub(r'[“”]', '"', cleaned_formula)
#             cleaned_formula = re.sub(r"[‘’]", "'", cleaned_formula)

#             # STEP 2: Replace field names with their alias versions
#             replaced_formula = cleaned_formula
#             for original, alias in alias_map.items():
#                 replaced_formula = replaced_formula.replace(original, alias)

#             print(f"→ Replaced with values: `{replaced_formula}`")

#             # STEP 3: Eval
#             result = eval(replaced_formula)
#             print(f" Result = {result}")

#             results.append({
#                 "assessment_criteria": criteria,
#                 "score": result,
#                 "weightage": weight
#             })

#         except Exception as e:
#             print(f" Failed to evaluate: {e}")
#             results.append({
#                 "assessment_criteria": criteria,
#                 "score": None,
#                 "weightage": weight,
#                 "error": str(e)
#             })

#     print("Final Computed Scores")
#     # print(pd.DataFrame(results), use_container_width=True)

# if __name__ == "__main__":
#     render("admin")

import re
import pandas as pd
from sqlalchemy import create_engine, text

# 1) Configure your DB connection
engine = create_engine("sqlite:///meinhardt.db", echo=False, future=True)

def evaluate_assessment(devco_id: str = "admin") -> pd.DataFrame:
    """
    Fetch submissions and assessment matrix for a given DevCo,
    normalize keys and formulas, then compute each score.
    Returns a DataFrame with columns:
      - assessment_criteria
      - score
      - weightage
      - error (if any)
    """
    # --- Fetch raw data ---
    with engine.begin() as conn:
        submissions = pd.read_sql(
            text("""
                SELECT data_point, field_name, value
                  FROM devco_submissions
                 WHERE devco_id = :devco_id
                 AND field_name = 'input_value'
            """),
            conn,
            params={"devco_id": devco_id}
        )
        matrix = pd.read_sql(text("SELECT * FROM assessment_matrix"), conn)

    if submissions.empty:
        raise ValueError(f"No submissions found for DevCo '{devco_id}'")

    # --- Build flat_inputs and alias_map ---
    flat_inputs = {}
    alias_map   = {}

    for _, row in submissions.iterrows():
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

    # Copy inputs into locals dict for eval()
    local_vars = dict(flat_inputs)
    # print(local_vars)
    
    # --- Evaluate each formula ---
    results = []
    for _, row in matrix.iterrows():
        criteria = row["assessment_criteria"]
        formula  = row["formula"]
        weight   = row["weightage"]

        # Step 1: normalize formula text
        cleaned = formula.replace("\xa0", " ")
        cleaned = re.sub(r"[“”]", '"', cleaned)
        cleaned = re.sub(r"[‘’]", "'", cleaned)
        cleaned = re.sub(r"\s*\(.*?\)", "", cleaned)  # strip parentheses
        # Step 2: replace human-readable keys with aliases
        expr = cleaned
        
        for raw_key, alias in alias_map.items():
            expr = expr.replace(raw_key, alias)

        # Step 3: eval safely
        try:
            score = eval(expr, {}, local_vars)
            error = None
        except Exception as e:
            score = None
            error = str(e)

        results.append({
            "assessment_criteria": criteria,
            "score":               score,
            "weightage":           weight,
            # "error":               error,
            "formula":            cleaned
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    import sys

    # Allow passing DevCo ID via CLI, default to "admin"
    devco = sys.argv[1] if len(sys.argv) > 1 else "admin"

    try:
        df = evaluate_assessment(devco)
        print(f"\nAssessment results for DevCo '{devco}':\n")
        print(df)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
