#!/bin/bash
# param 1 
sh_path=$(cd `dirname $0`; pwd)
docker_freeswitch_dir=${1:-/usr/local/freeswitch}

work_dir=${sh_path}/../
install_path=${sh_path}
work_freeswitch_dir=${work_dir}/freeswitch/
system_dir=${work_dir}/system_dir/
third_libs_dir=${work_dir}/third_libs/

module_load_conf_file=${work_dir}/module_load_conf
third_lib_install_param_file=${work_dir}/third_lib_install_param

modules_conf_xml_file_name="modules.conf.xml"
modules_conf_xml_file_path="${docker_freeswitch_dir}/conf/autoload_configs/${modules_conf_xml_file_name}"

as_conf_xml_file_name="as.conf.xml"
as_conf_xml_file_path="${docker_freeswitch_dir}/conf/autoload_configs/${as_conf_xml_file_name}"



function update_load_conf()
{
    local file_line
    local file
    local conf
    local mod
    local isok=0
    if [ ! -f ${module_load_conf_file} ];then
		return 0
	fi
    while read file_line
    do       
		tmp1=${file_line%,*}
		
		file=${tmp1%,*}
		conf=${tmp1#*,}
		mod=${file_line##*,}
		conf=${conf//<module_name>/${mod}}
        
        if [ -z "${file}" ] && [ -z "${mod}" ];then
            continue
        fi

        # modules.conf.xml module load
        if [ "${file}" = "${modules_conf_xml_file_name}" ];then
            line=`grep -n "^[[:blank:]]*<[[:blank:]]*load.*module=[[:blank:]]*\"${mod}\".*/>[[:blank:]]*$" ${modules_conf_xml_file_path} | awk -F':' '{print $1}'`            

            if [ -z "${line}" ];then
                sed -i 's?^.*</modules>.*$?'"${conf}"'\n</modules>?' ${modules_conf_xml_file_path}

            elif [ `echo ${line} | awk '{print NF}'` -eq 1 ];then
                sed -i "${line}"'s?^.*$?'"${conf}"'?' ${modules_conf_xml_file_path}

            else
        
                echo "${modules_conf_xml_file_name} : ${file_line} error"
                return 1
            fi 
                               
        elif [ "${file}" = "${as_conf_xml_file_name}" ];then
            line=`grep -n "^[[:blank:]]*<[[:blank:]]*module.*name=[[:blank:]]*\"${mod}\".*/>[[:blank:]]*$" ${as_conf_xml_file_path} | awk -F':' '{print $1}'`

            if [ -z "${line}" ];then
                sed -i 's?^.*</modules>.*$?'"${conf}"'\n</modules>?' ${as_conf_xml_file_path}
            elif [ `echo ${line} | awk '{print NF}'` -eq 1 ];then
                sed -i "${line}"'s?^.*$?'"${conf}"'?' ${as_conf_xml_file_path}
            
            else
                echo "${as_conf_xml_file_name} : ${file_line} error"
                return 1
            fi    
        else
            
            echo "${file_line} error"
            return 1
        fi
    
    done < ${module_load_conf_file} 
    return 0
}

function update_third_lib()
{
	if [ ! -f ${third_lib_install_param_file} ];then
		return 0
	fi
    while read file_line
    do     
		exec_file=${file_line%,*}
		lib_file=${file_line#*,}
        
		if [ ! -z "${exec_file}" ] && [ ! -z "${lib_file}" ];then
			exec_file=${install_path}/${exec_file}
			lib_file=${third_libs_dir}/${lib_file}
		else
			return 1
		fi
		
		if [ -f "${exec_file}" ] && [ -f "${lib_file}" ];then
			sh ${exec_file} ${lib_file}
			if [ $? -ne 0 ];then
				return 1
			fi
		else
			return 1
		fi    
    done < ${third_lib_install_param_file} 
    return 0
}

function copy_freeswitch_update_file()
{
    cp ${work_freeswitch_dir} $(dirname ${docker_freeswitch_dir}) -rf
    if [ $? -ne 0 ];then
        return 1
    fi    
    return 0
}

function copy_system_update_file()
{
	cp ${system_dir}/* / -rf
	if [ $? -ne 0 ];then
        return 1
    fi    
    return 0
}

copy_freeswitch_update_file
if [ $? -eq 1 ];then
    echo "copy_freeswitch_update_file error"
    exit 1
fi

copy_system_update_file
if [ $? -eq 1 ];then
    echo "copy_system_update_file error"
    exit 1
fi

update_load_conf
if [ $? -eq 1 ];then
        echo "update_load_conf error"
        exit 1
fi
update_third_lib
if [ $? -eq 1 ];then
	echo "update_third_lib error"
	exit 1
fi
exit 0
