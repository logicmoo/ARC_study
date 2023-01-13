FROM python:3.10-buster

RUN python3.10 -m pip install --upgrade pip

ADD requirements.txt requirements.txt
RUN python3.10 -m pip install -r requirements.txt

WORKDIR /streamlit/
RUN python3.10 -m pip install streamlit==1.9.0 protobuf==3.20.0

ADD requirements-dev.txt requirements-dev.txt
RUN python3.10 -m pip install -r requirements-dev.txt

ADD data data
ADD thumbnails thumbnails
ADD arc arc
ADD streamlit_app.py streamlit_app.py

CMD ["streamlit", "run", "--browser.serverAddress=0.0.0.0", "streamlit_app.py"]
