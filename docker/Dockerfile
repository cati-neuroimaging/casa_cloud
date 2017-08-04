FROM ubuntu:16.04 

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y flex bison dh-autoreconf xutils-dev libpciaccess0 libpciaccess-dev llvm libxext-dev libxdamage-dev libxfixes-dev libexpat1 libexpat1-dev libpthread-stubs0-dev curl pkg-config wget build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV GL_PROTO_CFLAG /usr/local/include/GL

RUN apt-get update && apt-get install -y git

RUN cd /tmp && \
    git clone https://github.com/JinpengLI/glproto.git && \
    cd glproto && ./autogen.sh && make && make install && \ 
    cd /tmp && \
    wget ftp://ftp.freedesktop.org/pub/mesa/mesa-17.0.0.tar.gz && \
    tar xvf mesa-17.0.0.tar.gz && \
    cd mesa-17.0.0 && \
    ./configure --enable-glx=xlib --disable-dri --disable-egl --with-gallium-drivers=swrast --disable-gbm --prefix=$HOME/mesa && \
    make -j3 && \
    make install && \
    cd .. && \
    rm -Rf mesa-17.0.0

RUN apt-get update && apt-get install -y libproxy-dev glib-networking-common
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && apt-get update && apt-get install -y tightvncserver wmaker x11-apps xfce4 xfce4-goodies
RUN cd /root/ && git clone https://github.com/novnc/noVNC.git && git clone https://github.com/kanaka/websockify noVNC/utils/websockify
RUN echo 'write password' > /tmp/pwd && \
    echo 'read password' >> /tmp/pwd && \
    mkdir $HOME/.vnc && \
    cat /tmp/pwd | vncpasswd -f > $HOME/.vnc/passwd && \
    chmod go-r $HOME/.vnc/passwd && \
    rm /tmp/pwd

RUN apt-get install -y apt-utils
RUN apt-get update && apt-get install -y python net-tools pyqt4-dev-tools python-pip python-dev build-essential python-numpy python-qt4-gl
 
RUN pip install six
ENV USER root
COPY vnc_xstartup /root/.vnc/xstartup
ENV LD_LIBRARY_PATH=/root/mesa/lib
RUN echo "LD_LIBRARY_PATH=/root/mesa/lib" >> $HOME/.bashrc
COPY docker_entrypoint /root/docker_entrypoint
CMD ["/root/docker_entrypoint"]

EXPOSE 8080
