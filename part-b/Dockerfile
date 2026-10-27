FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py corpus.py engine.py taxonomy.py evaluate.py review.py fresh_evaluate.py generate_fresh.py fresh2_evaluate.py generate_fresh2.py historical_review.py compare_versions.py ./
COPY data/development.jsonl data/review_reports.jsonl data/manifest.json ./data/
COPY data/reviewed_labels.jsonl data/reviewed_labels.freeze.json ./data/
COPY data/fresh_reports_20261022.jsonl data/fresh_labels_20261022.jsonl data/fresh_labels_20261022.freeze.json ./data/
COPY data/fresh2_reports_20261022.jsonl data/fresh2_labels_20261022.jsonl data/fresh2_labels_20261022.freeze.json ./data/
COPY evidence/ ./evidence/
COPY output/review/ ./output/review/
COPY web ./web
COPY tests ./tests
RUN python corpus.py && python -m unittest discover -s tests -v
RUN useradd --create-home relay && mkdir -p /state && chown relay:relay /state
USER relay
ENV RELAY_STATE_DIR=/state
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
