FROM python:3.10-buster

RUN python3.10 -m pip install --upgrade pip

ADD requirements.txt requirements.txt
RUN python3.10 -m pip install -r requirements.txt

WORKDIR /jupyterlab/
RUN python3.10 -m pip install jupyterlab
