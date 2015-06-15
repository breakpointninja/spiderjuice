#!/bin/bash

set -e
set -u
cd "$(dirname "$0")"
ROOT_DIRECTORY=$(pwd)

set +e
type deactivate >/dev/null 2>&1 && deactivate
set -e

rm -rf env
rm -rf packages

virtualenv --no-site-packages --python=python3 env
set +u
source env/bin/activate
set -u

mkdir -p packages
cd packages
PACKAGES_DIRECTORY=$(pwd)
wget -c http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.2/PyQt-gpl-5.4.2.tar.gz -O PyQt.tar.gz
wget -c http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.8/sip-4.16.8.tar.gz -O sip.tar.gz

mkdir -p pyqt
tar -xf PyQt.tar.gz -C ./pyqt
mkdir -p sip
tar -xf sip.tar.gz -C ./sip

cd ./sip/sip-4.16.8
SIP_DIRECTORY=$(pwd)
mkdir -p header

python configure.py "--incdir=${SIP_DIRECTORY}/header/"
make
make install

cd ${PACKAGES_DIRECTORY}/pyqt/PyQt-gpl-5.4.2
PYQT_DIRECTORY=$(pwd)
mkdir -p inst
python configure.py "--qmake=$(which qmake-qt5)" "--sip-incdir=${SIP_DIRECTORY}/header/" --confirm-license "--designer-plugindir=${PYQT_DIRECTORY}/inst" "--qml-plugindir=${PYQT_DIRECTORY}/inst"
make -j4
make install
