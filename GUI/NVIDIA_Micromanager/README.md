# Setting up Micro-Manager on NVIDIA JETSON
	
## OUTLINE
	* Install and prepare Jetson Jetpack
	* Download 
	* Download and compile micro-manager
	* Install Micro-manager

cd ..
MM_DIR=$(pwd)
cd micro-manager
sudo apt install python3.7-dev
wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
rm get-pip.py
pip3 install numpy --force-reinstall

git clone https://github.com/micro-manager/micro-manager.git
cd micro-manager

./autogen.sh
PYTHON=/usr/bin/python3
./configure --prefix=/opt/micro-manager --with-ij-jar=/home/bene/Downloads/ImageJ/ij.jar --with-python=/usr/include/python3.7 --with-boost-libdir=/usr/lib/aarch64-linux-gnu --with-boost=/usr/include/boost
make fetchdeps
make
sudo make install

make fetchdeps   # Required since SVN r14001-r14016

# Build binaries (can take a while)
make

# Install MM as ImageJ plugin
make install

?


# subversion build-essential \
# autoconf automake libtool pkg-config \
# libboost1.54-all-dev zlib1g-dev swig \
# openjdk-7-jdk ant python-dev python-numpy-dev


sudo apt-get install libboost-all-dev

bene@bene-desktop:~$ ./configure --prefix=$MM_DIR/ImageJ --enable-imagej-plugin=$MM_DIR/ImageJ --with-python --with-ij-jar=../ImageJ/ij.jar

make fetchdeps