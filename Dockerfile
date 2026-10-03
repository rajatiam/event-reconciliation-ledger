FROM python:3.13-slim
WORKDIR /app
COPY event_reconciliation_ledger ./event_reconciliation_ledger
RUN useradd --uid 10001 --create-home runner
USER runner
WORKDIR /workspace
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "event_reconciliation_ledger"]
CMD ["--help"]
