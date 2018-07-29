FROM nvidia/cuda:9.0-runtime-ubuntu16.04

RUN apt-get -y update && \
    apt-get -y install software-properties-common && \
    add-apt-repository ppa:jonathonf/python-3.6 && \
    apt-get -y update && \
    apt-get -y install \
                git \
                wget \
                libsm6 \
                libxext6 \
                python3.6-dev \
                libopenmpi-dev \
                python-pip \
                zlib1g-dev \
                python3-tk \
                cmake \
                # for chrome headless
                libappindicator1 libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 && \
     pip install virtualenv

ENV CODE_DIR /root/code
ENV VENV /root/venv

COPY requirements.txt $CODE_DIR/

RUN virtualenv $VENV --python=python3.6 && \
    . $VENV/bin/activate && \
    cd $CODE_DIR && \
    pip install -r requirements.txt

ENV PATH=$VENV/bin:$PATH
WORKDIR $CODE_DIR

COPY . .

CMD /bin/bash