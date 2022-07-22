FROM python:3.10-alpine3.16


WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN sudo apk add git

COPY . .

CMD [ "python", "./src/main.py" ]
