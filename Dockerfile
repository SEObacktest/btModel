# Use Python 3.7 as base image
FROM python:3.7.17-slim
# Set working directory in container

WORKDIR /app
COPY requirements.txt /app/
# Install dependencies
RUN pip install -r requirements.txt

# Copy all project files
COPY ./BackTrader .

# Command to run the script

CMD ["python",  "./BackTrader/main.py"]
