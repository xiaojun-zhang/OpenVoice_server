# Use an official Python runtime as a parent image
FROM continuumio/miniconda3:24.1.2-0

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory files to /app in the container
ADD . /app

# Clone the git repo
RUN git clone https://github.com/ValyrianTech/OpenVoice_server.git

# Set the working directory to OpenVoice
WORKDIR /app/OpenVoice_server

# Create a new conda environment with python 3.9 and activate it
RUN conda create -n openvoice python=3.9
RUN echo "source activate openvoice" > ~/.bashrc
ENV PATH /opt/conda/envs/openvoice/bin:$PATH

# Install the OpenVoice package and uvicorn for FastAPI
RUN pip install -e . uvicorn

# Install the OpenVoice package
RUN pip install -e .

# Download and extract the checkpoint file
RUN apt-get update && apt-get install -y unzip wget
RUN wget https://myshell-public-repo-hosting.s3.amazonaws.com/openvoice/checkpoints_1226.zip
RUN unzip checkpoints_1226.zip -d ./openvoice
RUN rm checkpoints_1226.zip

# Make port 8000 available to the world outside this container
EXPOSE 8000

RUN cd /app/OpenVoice_server/openvoice

# Run the FastAPI application when the container launches
CMD ["uvicorn", "openvoice.openvoice_server:app", "--host", "0.0.0.0", "--port", "8000"]
