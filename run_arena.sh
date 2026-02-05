docker build -t sat-bench-web .
docker run -p 8501:8501 -v "$(pwd)/solvers:/app/solvers" -v "$(pwd)/problems:/app/problems" -v "$(pwd)/results:/app/results" sat-bench-web