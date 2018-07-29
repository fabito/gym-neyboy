FROM nvidia/cuda:9.2-runtime-ubuntu16.04

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
                cmake &&  \
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