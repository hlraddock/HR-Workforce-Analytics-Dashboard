
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import math

st.set_page_config(
    page_title="HR People Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("HR People Intelligence Dashboard")

st.write(
    "An interactive workforce analytics and automation platform "
    "designed to support data-driven HR decisions."
)

st.caption(
    "Python | SQL | Pandas | Plotly | Streamlit | Gemini AI"
)

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

st.sidebar.caption("Use fictional data only.")

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
        "0": 0,
        "1.0": 1,
        "0.0": 0
    })
)

df = df.replace("", pd.NA)

missing_values = int(df.isna().sum().sum())

df = df.dropna()

invalid_records = (
    (df["salary"] <= 0) |
    (df["years_employed"] < 0) |
    (~df["salary"].map(math.isfinite)) |
    (~df["years_employed"].map(math.isfinite))
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

# Data quality report

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
    st.success("Cleaned records loaded into SQLite.")

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

active_count = int(
    (filtered["left_company"] == 0).sum()
)

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
    "Departure share describes the dataset, "
    "not an annual turnover rate."
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

# Automated workforce insights

st.header("Automated Workforce Insights")

max_departure = summary["departure_rate"].max()

highest_departments = summary.loc[
    summary["departure_rate"] == max_departure,
    "department"
].tolist()

departure_names = ", ".join(highest_departments)

highest_salary = summary.loc[
    summary["average_salary"].idxmax()
]

longest_tenure = summary.loc[
    summary["average_tenure"].idxmax()
]

insight1 = (
    f"Highest observed departure share: "
    f"{departure_names} ({max_departure:.1f}%). "
    "Collect additional information about employee departures."
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
    "These insights are rule-based and descriptive. "
    "They do not establish causation."
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
Duplicates Removed: {duplicates}

KEY WORKFORCE INSIGHTS

1. {insight1}
2. {insight2}
3. {insight3}

These are descriptive, rule-based insights.
No causal conclusions are established.

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

# Generative AI HR Assistant

st.divider()

st.header("AI HR Assistant")

st.write(
    "Ask questions about workforce trends, compensation, "
    "employee departures and HR strategy."
)

st.caption(
    "Powered by Google Gemini. Use fictional data only. "
    "AI responses should be reviewed by a human."
)

question = st.text_area(
    "Ask a question about your workforce",
    placeholder="What workforce trends should HR investigate?",
    max_chars=500
)

consent = st.checkbox(
    "I confirm that this dataset and my question contain "
    "only fictional information."
)

if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = ""

if st.button("Generate AI Insights"):

    st.session_state.ai_analysis = ""

    if not question.strip():
        st.warning("Please enter a question.")

    elif not consent:
        st.warning("Please confirm that you are using fictional data.")

    else:
        try:
            from google import genai

            api_key = st.secrets.get("GEMINI_API_KEY", "")

            if not api_key:
                st.error("Gemini API key is missing from Streamlit Secrets.")

            else:
                client = genai.Client(
                    api_key=api_key
                )

                workforce_context = summary.round(2).to_string(
                    index=False
                )

                prompt = f"""
You are an HR workforce analytics assistant.

Analyze this simulated aggregated workforce data:

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
Treat departure share as descriptive.
Acknowledge ties and limitations.
Keep the response professional and concise.
"""

                with st.spinner("Generating AI workforce analysis..."):

                    models = [
                        m.name
                        for m in client.models.list()
                        if m.name
                        and "flash" in m.name.lower()
                        and "generateContent" in (
                            m.supported_actions or []
                        )
                        and not any(
                            word in m.name.lower()
                            for word in [
                                "preview",
                                "experimental",
                                "image",
                                "audio",
                                "tts"
                            ]
                        )
                    ]

                    if not models:
                        st.warning("No compatible Gemini model found.")

                    else:
                        preferred = "models/gemini-2.5-flash"

                        if preferred in models:
                            model = preferred
                        else:
                            model = sorted(models)[0]

                        st.caption(f"AI model: {model}")

                        response = client.models.generate_content(
                            model=model,
                            contents=prompt
                        )

                        if response.text:
                            st.session_state.ai_analysis = response.text

                        else:
                            st.warning("No AI response was generated.")

        except Exception as e:
            st.error(
                f"AI request failed: {type(e).__name__}"
            )

            error_code = getattr(e, "code", "Unknown")

            st.write("Error code:", error_code)

            if str(error_code) == "400":
                st.warning("Check your API key and request settings.")

            elif str(error_code) == "403":
                st.warning("Check your Gemini API permissions.")

            elif str(error_code) == "404":
                st.warning("The selected AI model is unavailable.")

            elif str(error_code) == "429":
                st.warning("API usage limit reached. Try again later.")

            elif str(error_code) == "503":
                st.warning("Gemini is temporarily unavailable.")

if st.session_state.ai_analysis:

    st.subheader("AI Workforce Analysis")

    st.markdown(st.session_state.ai_analysis)

    st.download_button(
        "Download AI Analysis",
        data=st.session_state.ai_analysis,
        file_name="AI_HR_Analysis.txt",
        mime="text/plain"
    )

st.divider()

st.caption(
    "HR People Intelligence | Independent Portfolio Project | "
    "Simulated Workforce Analytics"
)
