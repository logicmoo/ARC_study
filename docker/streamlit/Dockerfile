FROM python:3.10-buster

RUN python3.10 -m pip install --upgrade pip

ADD requirements.txt requirements.txt
RUN python3.10 -m pip install -r requirements.txt

WORKDIR /streamlit/
RUN python3.10 -m pip install streamlit==1.2.0

ADD arc arc
ADD data data
ADD streamlit_app.py streamlit_app.py

CMD ["streamlit", "run", "--browser.serverAddress=0.0.0.0", "streamlit_app.py"]
