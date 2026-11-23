
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.set_page_config(
    page_title="HR People Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("HR People Intelligence Dashboard")

st.write("""
An interactive workforce analytics and automation platform
designed to support data-driven HR decisions through Python,
SQL, automated data validation, and workforce visualization.
""")

st.caption("Python | SQL | Pandas | Plotly | Streamlit")

# Generate simulated employee data

departments = ["HR", "Marketing", "Finance", "Operations"]

employees = []

for n in range(1, 101):
    employees.append({
        "employee_id": n,
        "department": departments[(n - 1) % 4],
        "salary": 45000 + ((n * 1379) % 65000),
        "years_employed": 1 + ((n * 7) % 12),
        "left_company": n % 5 == 0
    })

# Data ingestion

st.sidebar.header("Data Settings")

uploaded_file = st.sidebar.file_uploader(
    "Upload simulated employee CSV",
    type=["csv"]
)

st.sidebar.caption(
    "Use fictional or anonymized data only."
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        st.error("Unable to read CSV file.")
        st.stop()
else:
    df = pd.DataFrame(employees)

# Automated data validation

required_columns = [
    "employee_id",
    "department",
    "salary",
    "years_employed",
    "left_company"
]

missing_columns = [
    c for c in required_columns
    if c not in df.columns
]

if missing_columns:
    st.error(f"Missing columns: {missing_columns}")
    st.stop()

df = df[required_columns].copy()

original_count = len(df)

df["employee_id"] = (
    df["employee_id"].astype("string").str.strip()
)

df["department"] = (
    df["department"].astype("string").str.strip()
)

df["salary"] = pd.to_numeric(
    df["salary"], errors="coerce"
)

df["years_employed"] = pd.to_numeric(
    df["years_employed"], errors="coerce"
)

df["left_company"] = (
    df["left_company"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({
        "true": 1,
        "false": 0,
        "yes": 1,
        "no": 0,
        "1": 1,
        "0": 0
    })
)

df = df.replace("", pd.NA)

missing_values = int(df.isna().sum().sum())

df = df.dropna()

invalid_records = (
    (df["salary"] <= 0) |
    (df["years_employed"] < 0)
)

invalid_count = int(invalid_records.sum())

df = df[~invalid_records]

duplicates = int(
    df.duplicated(subset=["employee_id"]).sum()
)

df = df.drop_duplicates(subset=["employee_id"])

clean_count = len(df)

removed_count = original_count - clean_count

if df.empty:
    st.error("No valid employee records remain.")
    st.stop()

# SQL database integration

conn = sqlite3.connect(":memory:")

df.to_sql(
    "employees",
    conn,
    if_exists="replace",
    index=False
)

# Automated data quality report

st.header("Data Quality & Validation")

q1, q2, q3, q4 = st.columns(4)

q1.metric("Original Records", original_count)
q2.metric("Valid Records", clean_count)
q3.metric("Records Removed", removed_count)
q4.metric("Duplicates Removed", duplicates)

with st.expander("View data validation report"):
    st.write(f"Missing or unreadable values: {missing_values}")
    st.write(f"Invalid salary or tenure records: {invalid_count}")
    st.write(f"Duplicate employee IDs: {duplicates}")
    st.write("Cleaned records loaded into SQLite.")

# Department filters

available_departments = sorted(
    df["department"].unique().tolist()
)

selected = st.sidebar.multiselect(
    "Select Departments",
    options=available_departments,
    default=available_departments
)

if not selected:
    conn.close()
    st.warning("Select at least one department.")
    st.stop()

placeholders = ",".join(["?"] * len(selected))

# Query employee records using SQL

query = f"""
SELECT *
FROM employees
WHERE department IN ({placeholders})
"""

filtered = pd.read_sql_query(
    query,
    conn,
    params=selected
)

# SQL workforce summary

summary_query = f"""
SELECT
    department,
    COUNT(*) AS employees,
    AVG(salary) AS average_salary,
    AVG(years_employed) AS average_tenure,
    AVG(left_company) * 100 AS departure_rate,
    MIN(salary) AS minimum_salary,
    MAX(salary) AS maximum_salary
FROM employees
WHERE department IN ({placeholders})
GROUP BY department
"""

summary = pd.read_sql_query(
    summary_query,
    conn,
    params=selected
)

conn.close()

# Workforce metrics

st.header("Workforce Overview")

employee_count = len(filtered)
active_count = int((filtered["left_company"] == 0).sum())
average_salary = filtered["salary"].mean()
average_tenure = filtered["years_employed"].mean()
departure_rate = filtered["left_company"].mean() * 100
retention_share = 100 - departure_rate

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Employee Records", employee_count)
c2.metric("Active Employees", active_count)
c3.metric("Average Salary", f"${average_salary:,.0f}")
c4.metric("Average Tenure", f"{average_tenure:.1f} yrs")
c5.metric("Departure Share", f"{departure_rate:.1f}%")

st.caption(
    "Departure share describes the dataset, not an annual turnover rate."
)

# Workforce charts

st.header("Workforce Analytics")

left, right = st.columns(2)

with left:
    fig_salary = px.bar(
        summary,
        x="department",
        y="average_salary",
        color="department",
        title="Average Salary by Department"
    )

    st.plotly_chart(
        fig_salary,
        use_container_width=True
    )

with right:
    fig_departure = px.bar(
        summary,
        x="department",
        y="departure_rate",
        color="department",
        title="Employee Departures by Department"
    )

    st.plotly_chart(
        fig_departure,
        use_container_width=True
    )

left, right = st.columns(2)

with left:
    fig_tenure = px.bar(
        summary,
        x="department",
        y="average_tenure",
        color="department",
        title="Average Employee Tenure"
    )

    st.plotly_chart(
        fig_tenure,
        use_container_width=True
    )

with right:
    fig_headcount = px.pie(
        summary,
        names="department",
        values="employees",
        title="Employee Records by Department",
        hole=0.4
    )

    st.plotly_chart(
        fig_headcount,
        use_container_width=True
    )

salary_range = summary.melt(
    id_vars="department",
    value_vars=["minimum_salary", "maximum_salary"],
    var_name="Salary Type",
    value_name="Salary"
)

fig_range = px.bar(
    salary_range,
    x="department",
    y="Salary",
    color="Salary Type",
    barmode="group",
    title="Salary Range by Department"
)

st.plotly_chart(
    fig_range,
    use_container_width=True
)

# Automated rule-based workforce insights

st.header("Automated Workforce Insights")

highest_departure = summary.loc[
    summary["departure_rate"].idxmax()
]

highest_salary = summary.loc[
    summary["average_salary"].idxmax()
]

longest_tenure = summary.loc[
    summary["average_tenure"].idxmax()
]

insight1 = (
    f"Highest observed departure share: "
    f"{highest_departure['department']} "
    f"({highest_departure['departure_rate']:.1f}%). "
    "Investigate potential retention challenges."
)

insight2 = (
    f"Highest average compensation: "
    f"{highest_salary['department']} "
    f"(${highest_salary['average_salary']:,.0f}). "
    "Review differences in job levels and responsibilities."
)

insight3 = (
    f"Longest average tenure: "
    f"{longest_tenure['department']} "
    f"({longest_tenure['average_tenure']:.1f} years). "
    "Explore factors associated with employee longevity."
)

st.info(insight1)
st.info(insight2)
st.info(insight3)

st.caption(
    "Insights are rule-based, not generative AI. "
    "They identify patterns rather than establish causation. "
    "Ties may occur between departments."
)

# SQL results

st.header("SQL Department Summary")

st.dataframe(
    summary.round(2),
    use_container_width=True
)

with st.expander("View SQL query"):
    st.code(summary_query, language="sql")

# Employee records

st.header("Employee Records")

st.dataframe(
    filtered,
    use_container_width=True
)

# Automated leadership report

st.header("HR Leadership Report")

report = f"""
HR WORKFORCE INTELLIGENCE REPORT

Employee Records: {employee_count}
Active Employees: {active_count}
Average Salary: ${average_salary:,.2f}
Average Tenure: {average_tenure:.1f} years
Departure Share: {departure_rate:.1f}%
Active Employee Share: {retention_share:.1f}%

DATA QUALITY
Original Records: {original_count}
Valid Records: {clean_count}
Records Removed: {removed_count}

KEY WORKFORCE INSIGHTS
1. {insight1}
2. {insight2}
3. {insight3}

These are descriptive, rule-based insights.
No annual turnover rate or causal conclusion is established.

Generated using Python, SQL, Pandas and Streamlit.
"""

st.text(report)

st.download_button(
    "Download HR Leadership Report",
    data=report,
    file_name="HR_Leadership_Report.txt",
    mime="text/plain"
)

st.download_button(
    "Download Cleaned Employee Data",
    data=filtered.to_csv(index=False),
    file_name="cleaned_employee_data.csv",
    mime="text/csv"
)

st.divider()

st.caption(
    "HR People Intelligence | Independent Portfolio Project | "
    "Simulated Workforce Analytics"
)



# Generative AI HR Assistant

from google import genai

st.divider()

st.header("AI HR Assistant")

st.write("""
Ask questions about workforce trends, compensation,
employee departures, and HR strategy using generative AI.
""")

st.caption(
    "Powered by Google Gemini. Only use simulated data. "
    "AI responses should be reviewed by a human."
)

question = st.text_area(
    "Ask a question about your workforce",
    placeholder="What workforce trends should HR leadership investigate?",
    max_chars=500
)

if st.button("Generate AI Insights"):

    if not question.strip():
        st.warning("Please enter a question.")

    elif "GEMINI_API_KEY" not in st.secrets:
        st.error("AI API key has not been configured.")

    else:
        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"]
            )

            workforce_context = summary.round(2).to_string(
                index=False
            )

            prompt = f"""
You are an HR workforce analytics assistant.

Analyze the following simulated, aggregated workforce data:

{workforce_context}

User question:
{question}

Provide:
1. Key findings supported by the data.
2. Potential HR recommendations.
3. Additional information HR should collect.

Do not invent statistics.
Do not assume correlation means causation.
Do not make individual employment decisions.
Treat departure share as descriptive, not annual turnover.
Acknowledge ties and limitations.
Keep your response professional and concise.
"""

            with st.spinner("Analyzing workforce data..."):

                models = [
                    m.name for m in client.models.list()
                    if m.name
                    and "flash" in m.name.lower()
                    and "generateContent" in (
                        m.supported_actions or []
                    )
                    and not any(
                        x in m.name.lower()
                        for x in [
                            "preview", "experimental",
                            "image", "audio", "tts"
                        ]
                    )
                ]

                if not models:
                    st.warning("No compatible AI model found.")
                else:
                    model = sorted(models, reverse=True)[0]

                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )

                    if response.text:
                        st.subheader("AI Workforce Analysis")
                        st.markdown(response.text)

                        st.download_button(
                            "Download AI Analysis",
                            data=response.text,
                            file_name="AI_HR_Analysis.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("No text response was generated.")

        except Exception:
            st.error(
                "AI request failed. Check API access, "
                "model availability, and usage limits."
            )
