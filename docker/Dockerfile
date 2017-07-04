FROM ubuntu:16.04 

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y flex bison dh-autoreconf xutils-dev libpciaccess0 libpciaccess-dev llvm libxext-dev libxdamage-dev libxfixes-dev libexpat1 libexpat1-dev libpthread-stubs0-dev curl pkg-config wget build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV GL_PROTO_CFLAG /usr/local/include/GL

RUN apt-get update && apt-get install -y git

RUN cd /tmp && \
    git clone git://anongit.freedesktop.org/xorg/proto/glproto && \
    cd glproto && ./autogen.sh && make && make install && \ 
    cd /tmp && \
    wget ftp://ftp.freedesktop.org/pub/mesa/mesa-17.0.0.tar.gz && \
    tar xvf mesa-17.0.0.tar.gz && \
    cd mesa-17.0.0 && \
    ./configure --enable-glx=xlib --disable-dri --disable-egl --with-gallium-drivers=swrast --disable-gbm --prefix=$HOME/mesa && \
    make && \
    make install && \
    cd .. && \
    rm -Rf mesa-17.0.0

RUN apt-get update && apt-get install -y tightvncserver wmaker x11-apps net-tools

RUN cd /root/ && git clone https://github.com/novnc/noVNC.git && git clone https://github.com/kanaka/websockify noVNC/utils/websockify
RUN echo 'write password' > /tmp/pwd && \
    echo 'read password' >> /tmp/pwd && \
    mkdir $HOME/.vnc && \
    cat /tmp/pwd | vncpasswd -f > $HOME/.vnc/passwd && \
    chmod go-r $HOME/.vnc/passwd && \
    rm /tmp/pwd

RUN apt-get update && apt-get install -y python

COPY vnc_xstartup /home/brainvisa/.vnc/xstartup

ENV USER=brainvisa
ENV LD_LIBRARY_PATH=/home/brainvisa/mesa/lib
COPY docker_entrypoint /home/brainvisa/docker_entrypoint
CMD ["/home/brainvisa/docker_entrypoint"]

EXPOSE 8080
