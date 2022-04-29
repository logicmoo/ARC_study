FROM python:3.10-buster

RUN python3.10 -m pip install --upgrade pip

ADD requirements.txt requirements.txt
RUN python3.10 -m pip install -r requirements.txt

ADD requirements-dev.txt requirements-dev.txt
RUN python3.10 -m pip install -r requirements-dev.txt

WORKDIR /arc_study/
ADD arc arc
ADD tests tests
ADD data data

RUN echo "alias profile='python3.10 -m tests.profiler'" >> /root/.bashrc
RUN echo "alias pytest='python3.10 -m pytest tests'" >> /root/.bashrc
CMD ["pytest"]
