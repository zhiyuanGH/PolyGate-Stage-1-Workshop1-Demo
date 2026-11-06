FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY booking_demo ./booking_demo
COPY data/mock_data.json ./data/mock_data.json
RUN useradd --create-home sample && chown -R sample:sample /app
USER sample
EXPOSE 8000
CMD ["python", "-m", "booking_demo", "--host", "0.0.0.0", "--port", "8000"]
