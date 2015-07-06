#!/bin/bash

#################################################################
# Dependecies
#################################################################
# "@Development tools"
# gcc aria2 readline-devel sqlite-devel bzip2-devel lzma-devel openssl-devel gdbm-devel zlib-devel ncurses-devel tk-devel db4-devel libpcap-devel xz-devel
# qt5-qtbase-devel qt5-qtwebkit-devel
# xorg-x11-server-Xvfb
#################################################################
# centos extras
# epel-release
#################################################################


#################################################################
# Any subsequent commands which fail will cause the shell script to exit immediately
#################################################################
set -e
set -u

#################################################################
# cd to script directory
#################################################################
cd "$(dirname "$0")"
ROOT_DIRECTORY=$(pwd)

#################################################################
# Create pyenv directory
#################################################################
PYTHON_VERSION="3.4.3"
mkdir -p py_env
cd py_env
PYENV_PATH=$(pwd)

#################################################################
# Download python
#################################################################
if [ ! -f "Python-${PYTHON_VERSION}.tar.xz" ]; then
    aria2c -c --allow-overwrite=true -k 20M -k1M -x5 https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -o python-${PYTHON_VERSION}.new  && mv python-${PYTHON_VERSION}.new Python-${PYTHON_VERSION}.tar.xz
fi

#################################################################
# Extract python
#################################################################
if [ ! -d "Python-${PYTHON_VERSION}" ]; then
    tar -xf "Python-${PYTHON_VERSION}.tar.xz"
fi

#################################################################
# Install python
#################################################################
if [ ! -d "bin" ]; then
    cd "Python-${PYTHON_VERSION}"
    PYTHON_PATH=$(pwd)
    ./configure --prefix="${PYENV_PATH}" --with-pymalloc --with-doc-strings --with-threads
    make -j4
    make install
fi

PYTHON_BIN="${PYENV_PATH}/bin/python3"
PIP_BIN="${PYENV_PATH}/bin/pip3"

#################################################################
# Install all requirements
#################################################################
cd "${PYENV_PATH}"
${PIP_BIN} install -r "${ROOT_DIRECTORY}/requirements.txt"

#################################################################
# Check PyQT
#################################################################
cd "${PYENV_PATH}"

set +e
${PYTHON_BIN} -c "import PyQt5.QtWebKitWidgets, PyQt5.QtWidgets, PyQt5.QtCore, PyQt5.QtNetwork, PyQt5.QtWebKit"
EXISTS=$?
set -e

#################################################################
# Install PyQT
#################################################################
if [ ${EXISTS} -ne 0 ]; then
    mkdir -p packages
    cd packages
    PACKAGES_DIRECTORY=$(pwd)
    if [ ! -f "PyQt.tar.gz" ]; then
        aria2c -c --allow-overwrite=true -k1M -x5 http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.2/PyQt-gpl-5.4.2.tar.gz -o PyQt.tar.gz.new && mv PyQt.tar.gz.new PyQt.tar.gz
    fi
    if [ ! -f "sip.tar.gz" ]; then
        aria2c -c --allow-overwrite=true -k1M -x5 http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.8/sip-4.16.8.tar.gz -o sip.tar.gz.new && mv sip.tar.gz.new sip.tar.gz
    fi

    if [ ! -d "PyQt-gpl-5.4.2" ]; then
        tar -xf PyQt.tar.gz
    fi

    if [ ! -d "sip-4.16.8" ]; then
        tar -xf sip.tar.gz
    fi

    cd ${PACKAGES_DIRECTORY}/sip-4.16.8
    SIP_DIRECTORY=$(pwd)
    mkdir -p header

    ${PYTHON_BIN} configure.py "--incdir=${SIP_DIRECTORY}/header/"
    make
    make install

    cd ${PACKAGES_DIRECTORY}/PyQt-gpl-5.4.2
    PYQT_DIRECTORY=$(pwd)
    mkdir -p inst
    ${PYTHON_BIN} configure.py "--qmake=$(which qmake-qt5)" "--sip-incdir=${SIP_DIRECTORY}/header/" --confirm-license "--designer-plugindir=${PYQT_DIRECTORY}/inst" "--qml-plugindir=${PYQT_DIRECTORY}/inst" --sip="${PYENV_PATH}/bin/sip"
    make -j4
    make install
fi

#################################################################
# Final test to make sure PyQt5 webkit is installed
#################################################################
${PYTHON_BIN} -c "import PyQt5.QtWebKitWidgets, PyQt5.QtWidgets, PyQt5.QtCore, PyQt5.QtNetwork, PyQt5.QtWebKit"