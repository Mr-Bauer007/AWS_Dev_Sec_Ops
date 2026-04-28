FROM python:3.11-slim
# OWASP: Run as non-privileged user
RUN useradd -m appuser
WORKDIR /home/appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
