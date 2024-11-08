# Use Python 3.7 as base image
FROM python:3.7.17-slim
# Set working directory in container

WORKDIR /app

RUN env | grep -i _PROXY
# Install dependencies
RUN pip install numpy pandas backtrader optunity backtrader_plotting tushare

# Copy all project files
COPY . .

# Command to run the script
CMD ["python", "Bactrader_SystemV2.py"]