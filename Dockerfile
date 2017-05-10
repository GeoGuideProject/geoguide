FROM node:7

RUN apt-get update

RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN pyenv install 3.5.2
RUN pyenv global 3.5.2
RUN pyenv rehash

RUN mkdir /project
WORKDIR /project
ADD requirements.txt /project/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ADD . /project/

RUN npm install
