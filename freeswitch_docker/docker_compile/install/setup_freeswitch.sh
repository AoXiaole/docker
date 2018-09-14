workpath=$1
cd ${workpath}

function ERROR()
{
    echo "ERROR $1"
    exit 1
}

yum install -y autoconf automake libtool gcc-c++ ncurses-devel make zlib-devel libjpeg-devel yasm  nasm  libevent2-devel
yum install -y openssl-devel e2fsprogs-devel curl-devel pcre-devel speex-devel sqlite-devel mysql-devel
yum install -y git ldns-devel libedit-devel lua-devel libsndfile-devel libshout-devel lame-devel

chmod 777 * -R
sh support-d/prereq.sh || ERROR ${LINE}

cd libs
cd yasm

./autogen.sh || exit 1
./configure || exit 1
make && make install || ERROR ${LINE}

cd ..

cd opus

./autogen.sh || ERROR ${LINE}
./configure || ERROR ${LINE}

make && make install || ERROR ${LINE}

cp /usr/local/lib/pkgconfig/opus.pc /usr/lib64/pkgconfig -f || ERROR ${LINE}

cd ..

cd libpng

 ./configure || ERROR ${LINE}
make && make install || ERROR ${LINE}
cp /usr/local/lib/pkgconfig/libpng* /usr/lib64/pkgconfig/ 
cd ..

cd hiredis-vip

make && make install || ERROR ${LINE}

#tar xvf jemalloc-4.2.1.tar.bz2
#cd jemalloc-4.2.1
#./configure || ERROR ${LINE}
#make && make install || ERROR ${LINE}
#cd ..

cd ../../

./bootstrap.sh -j || ERROR ${LINE}
./configure --disable-libyuv --disable-libvpx || ERROR ${LINE}

cd src/mod/codecs/mod_g729/
make  || ERROR ${LINE}
cd ../../../../


cd libs/unimrcp/libs/apr-toolkit
make && make install || ERROR ${LINE}
cd ../../../../
make && make install || ERROR ${LINE}

