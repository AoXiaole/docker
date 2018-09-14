sh_path=$(cd `dirname $0`; pwd)
tar_mongodb=$1
mongodb_work=${sh_path}/mongodb_work
cd ${sh_path}
mkdir ${mongodb_work}
tar -xvf ${tar_mongodb} -C ${mongodb_work}
cd ${mongodb_work}
cd mongo-c-driver-1.9.5
./configure --disable-automatic-init-and-cleanup && make && make install
if [ $? -ne 0 ];then
	echo "mongodb : ./configure --disable-automatic-init-and-cleanup && make && make install failed"
	exit 1
fi
cd ../../
rm ${mongodb_work} -rf
exit 0