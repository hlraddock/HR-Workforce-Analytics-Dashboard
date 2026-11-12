
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="HR Analytics Dashboard",
    layout="wide"
)

st.title("HR Workforce Analytics Dashboard")
st.write("""
This interactive HR Analytics Dashboard analyzes a simulated
workforce of 100 employees across four departments.

The project explores compensation, employee tenure, workforce
retention, and employee departures to demonstrate how Python
can support data-driven HR decisions.

Tools: Python, Pandas, Plotly, and Streamlit.
""")

# Generate 100 fictional employees
employees = []

departments = ["HR", "Marketing", "Finance", "Operations"]

for n in range(1, 101):
    employees.append({
        "employee_id": n,
        "department": departments[(n - 1) % 4],
        "salary": 45000 + ((n * 1379) % 65000),
        "years_employed": 1 + ((n * 7) % 12),
"left_company": n % 5 == 0
    })

df = pd.DataFrame(employees)
from pathlib import Path

df.to_csv(Path(__file__).resolve().parent / "employees.csv", index=False)

# Interactive department filter
selected = st.multiselect(
    "Select departments:",
    options=departments,
    default=departments
)

filtered = df[df["department"].isin(selected)]

# Dashboard metrics
col1, col2, col3 = st.columns(3)

col1.metric("Employees", len(filtered))
col2.metric(
    "Average Salary",
    f"${filtered['salary'].mean():,.0f}"
    if not filtered.empty else "N/A"
)
col3.metric(
    "Average Tenure",
    f"{filtered['years_employed'].mean():.1f} years"
    if not filtered.empty else "N/A"
)

# Salary chart
salary_data = (
    filtered.groupby("department", as_index=False)["salary"]
    .mean()
)

fig = px.bar(
    salary_data,
    x="department",
    y="salary",
    title="Average Salary by Department",
    labels={"salary": "Average Salary ($)"}
)

st.plotly_chart(fig, use_container_width=True)

# Employee data
st.subheader("Employee Data")
st.dataframe(filtered, use_container_width=True)
# Employee Turnover Analysis
st.subheader("Employee Turnover Analysis")

turnover_rate = filtered["left_company"].mean() * 100 if not filtered.empty else 0

st.metric("Employee Turnover Rate", f"{turnover_rate:.1f}%")
# Turnover Rate by Department
turnover_by_department = (
    filtered.groupby("department", as_index=False)["left_company"]
    .mean()
)

turnover_by_department["turnover_rate"] = (
    turnover_by_department["left_company"] * 100
)

fig_turnover = px.bar(
    turnover_by_department,
    x="department",
    y="turnover_rate",
    title="Employee Turnover Rate by Department",
    labels={"turnover_rate": "Turnover Rate (%)"}
)

st.plotly_chart(fig_turnover, use_container_width=True)
# Salary Range by Department
salary_range = (
    filtered.groupby("department", as_index=False)["salary"]
    .agg(["min", "max"])
    .reset_index()
)

salary_range = salary_range.melt(
    id_vars="department",
    value_vars=["min", "max"],
    var_name="Salary Type",
    value_name="Salary"
)

fig_salary_range = px.bar(
    salary_range,
    x="department",
    y="Salary",
    color="Salary Type",
    barmode="group",
    title="Minimum vs Maximum Salary by Department"
)

st.plotly_chart(fig_salary_range, use_container_width=True)
# Employee Retention Analysis
st.subheader("Employee Retention Analysis")

retention_rate = (
    (1 - filtered["left_company"].mean()) * 100
    if not filtered.empty else 0
)

st.metric("Employee Retention Rate", f"{retention_rate:.1f}%")
# Download Employee Data
st.subheader("Download HR Data")

st.download_button(
    label="Download Employee Data (CSV)",
    data=filtered.to_csv(index=False),
    file_name="hr_employee_data.csv",
    mime="text/csv"
)
