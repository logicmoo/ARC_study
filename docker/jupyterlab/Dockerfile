FROM python:3.10-buster

RUN python3.10 -m pip install --upgrade pip
RUN python3.10 -m pip install jupyterlab

WORKDIR /jupyterlab/
ADD requirements.txt requirements.txt
RUN python3.10 -m pip install -r requirements.txt

# This resolves a conflict with NumPy's versioning
RUN python3.10 -m pip install --upgrade numpy
