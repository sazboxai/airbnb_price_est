FROM python:3.9

MAINTAINER sebastian cajamarca

COPY . /code

WORKDIR /code

RUN pip install -r requirements.txt

EXPOSE 8080

CMD python dashboard.py