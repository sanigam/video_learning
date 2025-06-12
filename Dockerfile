FROM python:3.11-slim
ENV HOST=0.0.0.0
WORKDIR /app
# Upgrade pip and install requirements
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
EXPOSE 8080
# Copy app code and set working directory
COPY . /app
CMD ["streamlit", "run", "main.py", "--server.port", "8080"]