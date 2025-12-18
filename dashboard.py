import streamlit as st
import plotly.express as px
import pandas as pd
import os

# --- Configuration ---
RESULTS_FILE = "/app/results/benchmark_data.csv"

st.set_page_config(page_title="SAT Benchmark Results", layout="wide")

st.title("SAT Solver Benchmark Results")

if not os.path.exists(RESULTS_FILE):
    st.error(
        f"Results file not found at {RESULTS_FILE}. Please run your benchmark script first.")
    st.stop()

# Load Data
df = pd.read_csv(RESULTS_FILE)

# --- Top Level Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Problems", df['problem'].nunique())
col2.metric("Solvers Tested", df['solver'].nunique())
col3.metric("Total Time", f"{df['wall_sec'].sum():.2f}s")

# --- Interactive Data Table ---
st.subheader("Detailed Data")


def highlight_status(val):
    color = 'green' if val == 'SAT' or val == 'UNSAT' else 'red'
    return f'color: {color}'


st.dataframe(
    df.style.map(highlight_status, subset=['status']),
    width='stretch',
    height=400
)

# --- Interactive Charts ---
st.subheader("Performance Analysis")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Wall Time", "CPU Time", "Memory Usage", "Correctness"])

with tab1:
    st.markdown("### Execution Time (Seconds)")
    # Pivot data for the chart: Index=Problem, Columns=Solver, Values=Metric
    use_log1 = st.checkbox("Use Log Scale", value=False, key="log_time")

    fig = px.bar(
        df,
        x="problem",
        y="wall_sec",
        color="solver",
        barmode="group",
        log_y=use_log1,
        hover_data=["status", "memory_kb"],
        title="Solver Comparison by Problem"
    )

    st.plotly_chart(fig, width='stretch')

with tab2:
    st.markdown("### CPU Time (Seconds)")
    # Pivot data for the chart: Index=Problem, Columns=Solver, Values=Metric
    use_log2 = st.checkbox("Use Log Scale", value=False, key="log_cpu")

    fig = px.bar(
        df,
        x="problem",
        y="cpu_sec",
        color="solver",
        barmode="group",
        log_y=use_log2,
        hover_data=["status", "memory_kb"],
        title="Solver Comparison by Problem"
    )

    st.plotly_chart(fig, width='stretch')

with tab3:
    st.markdown("### Memory Usage (KB)")

    use_log3 = st.checkbox("Use Log Scale", value=False, key="log_mem")

    fig = px.bar(
        df,
        x="problem",
        y="memory_kb",
        color="solver",
        barmode="group",
        log_y=use_log3,
        hover_data=["status", "wall_sec"],
        title="Solver Comparison by Problem"
    )

    st.plotly_chart(fig, width='stretch')

    mem_data = df.pivot(index='problem', columns='solver', values='memory_kb')
    st.bar_chart(mem_data)

with tab4:
    st.markdown("### Correctness Note")
    st.dataframe(
        df[["problem", "solver", "correct", "note"]],
        width='stretch',
    )
