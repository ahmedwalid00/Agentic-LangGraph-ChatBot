# Step 1: Start from an official Python base image.
# We use python:3.11 to match your Conda environment. 'slim' is a smaller version.
FROM python:3.11-slim

# Step 2: Set the working directory inside the container.
# All subsequent commands will run from /app.
WORKDIR /app

# Step 3: Copy only the requirements file first.
# This is a Docker caching optimization. This step only re-runs if requirements.txt changes.
COPY requirements.txt .

# Step 4: Install the Python dependencies.
# --no-cache-dir makes the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of your application code into the container.
# This includes your 'src' and 'static' folders.
COPY . .

# Step 6: Define the command to run your application.
# This is the same command we used for Render's "Start Command" before.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]