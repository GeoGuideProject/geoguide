FROM node:7

RUN \
  apt-get update && \
  apt-get install -y curl

RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

RUN /root/.pyenv/bin/pyenv install 3.5.2
RUN /root/.pyenv/bin/pyenv global 3.5.2

RUN mkdir /project
WORKDIR /project
ADD requirements.txt /project/

RUN /root/.pyenv/versions/3.5.2/bin/pip install --upgrade pip
RUN /root/.pyenv/versions/3.5.2/bin/pip install -r requirements.txt
ADD . /project/

RUN npm install

RUN /root/.pyenv/versions/3.5.2/bin/python manage.py create_db
