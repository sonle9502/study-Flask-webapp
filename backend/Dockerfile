# Use a Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# ここでデータベースのマイグレーションを実行
RUN flask db upgrade

# Expose port
EXPOSE 5000

# Start the application
CMD ["flask", "run", "--host=0.0.0.0"]
