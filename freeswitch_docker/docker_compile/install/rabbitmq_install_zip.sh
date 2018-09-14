sh_path=$(cd `dirname $0`; pwd)
tar_rabbitmq=$1
cd ${sh_path}
which zip
if [ $? -ne 0 ];then
	yum install -y zip
	if [ $? -ne 0 ];then
		echo "yum install -y zip error"
		exit 1
	fi
fi

unzip ${tar_rabbitmq}
cd AMQP-CPP-master
make && make install
if [ $? -ne 0 ];then
	echo "AMQP-CPP-master :  make && make install failed"
	exit 1
fi
cd ../
rm  AMQP-CPP-master -rf
exit 0