FROM ubuntu

ENV AUTORECONF=false
ENV LANG=C.UTF-8

COPY . /omorfi
WORKDIR /omorfi
RUN apt-get update

RUN apt-get install -y wget
RUN wget https://apertium.projectjj.com/apt/install-release.sh -O - | bash

RUN apt-get install -y \
    autoconf \
    automake \
    libtool \
    g++ \
    hfst \
    libhfst-dev \
    make \
    pkgconf \
    python3 \
    python3-libhfst \
    zip

RUN ./autogen.sh
RUN autoreconf -i -f
RUN ./configure
RUN make
RUN make install

RUN src/bash/omorfi-download.bash

RUN ./configure --enable-segmenter --enable-labeled-segments --enable-lemmatiser
RUN make
RUN make install
ENV PYTHONPATH=/omorfi/src/python
