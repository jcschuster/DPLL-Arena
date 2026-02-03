import streamlit as st
import pandas as pd
import os
import plotly.express as px
import engine

# --- CONFIG ---
RESULTS_DIR = "/app/results"
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_data.csv")
SOLVERS_DIR = "/app/solvers"
PROBLEMS_DIR = "/app/problems"

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SOLVERS_DIR, exist_ok=True)
os.makedirs(PROBLEMS_DIR, exist_ok=True)

st.set_page_config(page_title="SAT Arena", layout="wide")
st.title("AISE-LKR-B: SAT-Arena - Interactive Benchmark")

# --- SIDEBAR: Configuration ---
with st.sidebar:
    st.header("Configuration")
    uploaded_solvers = st.file_uploader(
        "Upload Solvers (.py, .ex, binary)", accept_multiple_files=True)
    if uploaded_solvers:
        for up_file in uploaded_solvers:
            with open(os.path.join(SOLVERS_DIR, up_file.name), "wb") as f:
                f.write(up_file.getbuffer())
        st.success(f"Uploaded {len(uploaded_solvers)} solvers.")

    uploaded_problems = st.file_uploader(
        "Upload Problems (.cnf)", accept_multiple_files=True)
    if uploaded_problems:
        for up_file in uploaded_problems:
            with open(os.path.join(PROBLEMS_DIR, up_file.name), "wb") as f:
                f.write(up_file.getbuffer())
        st.success(f"Uploaded {len(uploaded_problems)} problems.")

    if st.button("Clear Previous Results"):
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
            st.warning("Results cleared.")

# --- MAIN: Control Panel ---
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Control")
    solvers = [f for f in os.listdir(SOLVERS_DIR) if not f.startswith('.')]
    problems = [f for f in os.listdir(PROBLEMS_DIR) if f.endswith(
        '.cnf') and not f.startswith('.')]

    st.info(f"Detected: {len(solvers)} Solvers, {len(problems)} Problems")

    start_btn = st.button("START BENCHMARK", type="primary", width='stretch')

# --- EXECUTION LOGIC ---
if start_btn:
    if not solvers or not problems:
        st.error("Please ensure you have both solvers and problems uploaded.")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        live_table = st.empty()

        total_steps = len(solvers) * len(problems)
        current_step = 0

        for prob_name in problems:
            prob_path = os.path.join(PROBLEMS_DIR, prob_name)

            expected = "UNKNOWN"
            if prob_name.startswith("uf") or prob_name.startswith("bw_"):
                expected = "SAT"
            elif prob_name.startswith("uuf") or prob_name.startswith("ram_"):
                expected = "UNSAT"

            for solver_name in solvers:
                current_step += 1
                progress = current_step / total_steps
                progress_bar.progress(progress)
                status_text.markdown(
                    f"**Running:** `{solver_name}` on `{prob_name}`...")

                solver_path = os.path.join(SOLVERS_DIR, solver_name)

                stdout, stderr, code, wall_time_sec, cpu_time_sec = engine.run_solver(
                    solver_path, prob_path)

                try:
                    mem, duration, cpu, status, model = engine.parse_output(
                        stdout, stderr, code, wall_time_sec, cpu_time_sec)
                except Exception as e:
                    status = "ERROR"
                    mem, duration, cpu, model = 0, 0, 0, None

                is_correct, note = engine.verify_correctness(
                    prob_path, status, model, expected)

                results.append({
                    "solver": solver_name,
                    "problem": prob_name,
                    "status": status,
                    "wall_ms": duration,
                    "cpu_ms": cpu,
                    "memory_kb": mem,
                    "correct": is_correct,
                    "note": note
                })

                live_table.dataframe(pd.DataFrame(results)[::-1])

        df = pd.DataFrame(results)
        df.to_csv(RESULTS_FILE, index=False)
        st.success("Benchmark Run Complete!")
        st.rerun()  # Refresh to show analysis tabs

# --- ANALYSIS TABS (Only show if results exist) ---
if os.path.exists(RESULTS_FILE):
    df = pd.read_csv(RESULTS_FILE)

    st.divider()
    st.header("Results Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Overview", "Time", "Memory", "Raw Data"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Problems", df['problem'].nunique())
        c2.metric("Solvers", df['solver'].nunique())
        c3.metric("Avg Wall Time", f"{round(df['wall_ms'].mean())}ms")

        st.subheader("Correctness Status")
        st.dataframe(df.style.apply(lambda x: [
                     'background: #ffcdd2' if v is False else '' for v in x], subset=['correct']))

    with tab2:
        st.subheader("Execution Time")
        fig = px.bar(df, x="problem", y="wall_ms",
                     color="solver", barmode="group", log_y=True)
        st.plotly_chart(fig, width='stretch')

    with tab3:
        st.subheader("Memory Usage")
        fig = px.bar(df, x="problem", y="memory_kb",
                     color="solver", barmode="group")
        st.plotly_chart(fig, width='stretch')

    with tab4:
        st.dataframe(df)
