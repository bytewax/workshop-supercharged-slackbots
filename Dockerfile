# Start from a debian slim with python support
FROM python:3.11-slim-bullseye
# Setup a workdir where we can put our dataflow
WORKDIR /bytewax
# Install bytewax and the dependencies you need here
# Copy the dataflow in the workdir
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY dataflow.py dataflow.py
COPY .env .env
COPY utils utils
COPY data data
# And run it.
# Set PYTHONUNBUFFERED to any value to make python flush stdout,
# or you risk not seeing any output from your python scripts.
ENV PYTHONUNBUFFERED 1
CMD ["python", "-m", "bytewax.run", "dataflow"]
