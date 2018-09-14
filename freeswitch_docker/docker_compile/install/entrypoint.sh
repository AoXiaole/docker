#!/bin/bash
/usr/local/freeswitch/bin/freeswitch -nosql -nonat -ncwait -nonatmap -nocal -nort

while [ 1 -eq 1 ]
do
	ps_value=`ps -ef | grep '/usr/local/freeswitch/bin/freeswitch' | grep -v grep`
	if [ -z "${ps_value}" ];then
		break		
	else
		sleep 5
	fi
done
exit 0
