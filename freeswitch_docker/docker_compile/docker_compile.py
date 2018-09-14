#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
import sys,os,platform
import shutil,datetime,hashlib
from platform import system as osys

class g_global:
	'''
	version_str="version"
	descriptin_str="description"
	mod_libs_str="libs"

	dependence_str="dependence"
	dialplan_xmls_str="dialplan_xmls"
	freeswitch_files_str="freeswitch_files"
	docker_name_str="docker_name"
	tag_str="tag"
	base_image_str="base_image"
	modules_str="modules"
	third_libs_str="third_libs"
	libfile_str="libfile"
	install_str="install"
	system_files_str="system_files"
    '''

	pid=os.getpid()
	
	#{module1:info,modules2:info,modules3:info}
	mod_yaml_json={}
	# 保存一个configure的配置
	configure_yaml_json={}
#	docker_name=""
	base_image_name=""
	image_name=""
	image_tag=""
	add_moduls=[]

	install_param_list = [] #["install_sh,libfile.tar.gz","install_sh,libfile.tar.gz"]
	modules_load_conf=[] 	# 模块加载的配置
	copy_file_list=[]

	compiled_list=[] 	#已经编译了的模块
	load_libs={}		#需要加载的库的列表

	packet_dir = os.path.split(os.path.realpath(sys.argv[0]))[0] # 本脚本所在目录
	mod_dir = os.path.join(packet_dir, "../") # 根路径
	config_dir = os.path.join(mod_dir, "config/") # 配置文件所在目录
	script_dir = os.path.join(packet_dir, "script/") # 脚本所在目录
	src_code_dir = os.path.join(packet_dir, "../../../../") # fs源码路径
	src_install_dir = os.path.join(packet_dir, "install/")
	dockerfile_sample_file = ""


	tmp_work_dir = os.path.join(packet_dir, "work_" + str(pid) + "/") # 临时的打包目录
	tmp_freeswitch_dir = tmp_work_dir + "freeswitch/"
	tmp_dialplan_dir = tmp_freeswitch_dir + "conf/dialplan"
	tmp_install_dir = tmp_work_dir + "install/"
	tmp_third_libs_dir = tmp_work_dir + "third_libs/"
	tmp_system_files_dir = tmp_work_dir + "system_dir/"
	dockerfile_file = tmp_work_dir + "Dockerfile"

	module_load_conf_file = "module_load_conf"	# 模块加载列表文件
	third_lib_install_param_file = "third_lib_install_param"
	update_sh_file_src = packet_dir + "/install/update_docker.sh"
	update_sh_file_des_path = tmp_install_dir


def color_str(s, color = 'white', need = True):
	if osys() in ['Linux'] and need:
		color_code = color.lower() == 'red' and 91 or \
			color.lower() == 'yellow' and 93 or \
			color.lower() == 'blue' and 94 or \
			color.lower() == 'green' and 92 or \
			color.lower() == 'purple' and 95 or \
			color.lower() == 'gray' and 90 or \
			color.lower() == 'sky_blue' and 36 or \
			97
		return '\033[0m\033[' + str(color_code) + 'm' + s + '\033[0m'
	else:
		return s
		
# yaml包要先安装
try:
	import yaml
except ImportError as err:
	if "No module named" in str(err):
		print(color_str("this script base on PyYaml, I will install it first, please wait a moment", "purple"))
		result = os.system("yum -y install PyYAML")
		if 0 != result:
			print(color_str("sorry, there have some problems on auto-install PyYaml, please install it manually", "red"));
			sys.exit(result)
		else:
			import yaml

########################################################################################
# 优化json数据，将字典的值None节点删除，避免get到none数据后再操作引起的报错
def optimize_dict(this_dict):
	for key in this_dict.keys():
		# 是字典
		if isinstance(this_dict[key], dict):
			optimize_dict(this_dict[key])
		# 是列表
		elif isinstance(this_dict[key], list):
			optimize_list(this_dict[key])
		# 是None
		elif this_dict[key] is None:
			this_dict.pop(key)

	return 0

def optimize_list(this_list):
	for value in this_list:
		# 是字典
		if isinstance(value, dict):
			optimize_dict(value)
		# 是列表
		elif isinstance(value, list):
			optimize_list(value)

def load_yaml_file(config_file):
	g_global.configure_yaml_json = yaml.load(open(os.path.join(g_global.packet_dir, config_file)))
	if g_global.configure_yaml_json is None:
		print(color_str(sys.argv[1] + " file, syntactic error", "red"))
		return False


	path = g_global.packet_dir + "/mod"
	pathDir = os.listdir(path)
	for allDir in pathDir:
		child = os.path.join('%s/%s' % (path, allDir))
		dicts = yaml.load(open(child))
		for k in dicts:
			g_global.mod_yaml_json[k] = dicts[k]

	optimize_dict(g_global.configure_yaml_json)
	optimize_dict(g_global.mod_yaml_json)

	return True

def add_mod_to_list(mod_name):
	if mod_name in g_global.add_moduls:
		return 0
	libs = g_global.mod_yaml_json.get(mod_name,{}).get("libs",{})
	for libs_key in libs.keys():
		for dep_mod in libs[libs_key].get("dependence",[]):
			add_mod_to_list(dep_mod)

	g_global.add_moduls += [mod_name]
	return 0


def yaml_conf_ini(config_yaml_file):
	# 加载 mod/*.yaml 和 config_yaml
	if not load_yaml_file(config_yaml_file):
		print(color_str("load_yaml_file error!", "red"))
		return False

	g_global.base_image_name = g_global.configure_yaml_json.get("base_image" ,"")
	g_global.image_name = g_global.configure_yaml_json.get("image","")
	g_global.image_tag = g_global.configure_yaml_json.get("tag","")
	g_global.dockerfile_sample_file = g_global.configure_yaml_json.get("dockerfile", "")
	g_global.dockerfile_sample_file = g_global.packet_dir + "/install/" + g_global.dockerfile_sample_file

	# 将其中的依赖库也全部找出
	for mod in g_global.configure_yaml_json.get("modules",[]):
		add_mod_to_list(mod)

	if not (g_global.base_image_name and g_global.image_name and g_global.image_tag and g_global.dockerfile_sample_file):
		print(color_str("base_image , image , tag ,dockerfile have null!", "red"))
		return False

	# 将 third_libs 列表的复制文件列表加入到 g_global.copy_file_list
	third_libs = g_global.configure_yaml_json.get("third_libs",{})
	for lib in third_libs.keys():
		#g_global.third_file_list += [third_libs.get(lib,{}).get("libfile","")]
		#g_global.install_file_list += [third_libs.get(lib,{}).get("install","")]
		libfile = third_libs.get(lib,{}).get("libfile","")
		install = third_libs.get(lib,{}).get("install","")
		if libfile and install:
			libfile_path = g_global.src_code_dir + libfile
			install_path = g_global.src_install_dir + install
			g_global.copy_file_list += [[libfile_path, g_global.tmp_third_libs_dir]]
			g_global.copy_file_list += [[install_path, g_global.tmp_install_dir]]
			g_global.install_param_list += [install + "," + \
											libfile.split("/")[-1]]

	# 将 configure下的system_files 列表的复制文件列表加入到 g_global.copy_file_list
	for file_list in g_global.configure_yaml_json.get("system_files", []):
		f_list = file_list.split(',')
		src = g_global.src_code_dir + f_list[0]
		des = g_global.tmp_system_files_dir + f_list[1]
		g_global.copy_file_list += [[src, des]]

	# 将reeswitch_files 列表的复制文件列表加入到 g_global.copy_file_list
	for mod_name in g_global.add_moduls:
		for file_list in g_global.mod_yaml_json.get(mod_name,{}).get("freeswitch_files",[]):
			f_list = file_list.split(',')
			src = g_global.src_code_dir + f_list[0]
			des = g_global.tmp_freeswitch_dir + f_list[1]
			g_global.copy_file_list += [[src, des]]

	# 将 conf 列表的复制文件列表加入到 g_global.copy_file_list
	for mod_name in g_global.add_moduls:
		for file in g_global.mod_yaml_json.get(mod_name, {}).get("config", []):
			src = g_global.config_dir + file
			g_global.copy_file_list += [[src, g_global.tmp_dialplan_dir]]


	# 将 mod下的system_files 列表的复制文件列表加入到 g_global.copy_file_list
	for mod_name in g_global.add_moduls:
		for file_list in g_global.mod_yaml_json.get(mod_name,{}).get("system_files",[]):
			f_list = file_list.split(',')
			src = g_global.src_code_dir + f_list[0]
			des = g_global.tmp_system_files_dir + f_list[1]
			g_global.copy_file_list += [[src, des]]

	# 将 load_libs 列表初始化
	for mod_name in g_global.add_moduls:
		mod_dir = g_global.mod_yaml_json.get(mod_name,{}).get("mod_dir", mod_name)
		lib_keys = g_global.mod_yaml_json.get(mod_name,{}).get("libs", {}).keys()
		if lib_keys:
			g_global.load_libs[mod_dir] = lib_keys

	#将modules_load_conf 列表初始化
	for mod_name in g_global.add_moduls:
		libs = g_global.mod_yaml_json.get(mod_name,{}).get("libs", {})
		for key in libs.keys():
			load_conf = libs[key].get("load_conf","")
			if load_conf:
				g_global.modules_load_conf += [load_conf + "," + key]

	return True

def compile_one_mod(mod_name):
	mod_info = g_global.mod_yaml_json.get(mod_name)
	if mod_info is None:  # 模块不存在
		print(color_str("complie_module '" + mod_name + "' is not exist", "red"))
		return False

	if mod_name in g_global.compiled_list:  # 模块已经被编译
		print(color_str("complie_module '" + mod_name + "' is compiled", "blue"))
		return True

	mod_dir = g_global.mod_yaml_json.get(mod_name,{}).get("mod_dir", mod_name)


	print(color_str("\ncompiling mod '" + mod_name + "' ...", "purple"))
	mod_path = os.path.join(g_global.mod_dir, mod_dir)
	if not os.path.exists(mod_path):
		print(color_str("mod path '" + mod_path + "' not exists, please check your config", "red"))
		return False
	result = os.system("cd " + mod_path + " && " + "make clean && make ")
	if result != 0:
		print(color_str("compile mod '" + mod_name + "' failed", "red"))
		return False

	print(color_str("complie_module '" + mod_name + "' success", "blue"))
	g_global.compiled_list += [mod_name]
	return True


def compile_modules():
	for mod_name in  g_global.add_moduls:
		if not compile_one_mod(mod_name):
			print(color_str("compile_one_mod '" + mod_name +"' failed", "red"))
			return False
	return True


def copy_file():

	isExists=os.path.exists(g_global.tmp_work_dir)
	if isExists:
		os.system("rm " + g_global.tmp_work_dir + " -rf")

	fs_conf_dir = g_global.tmp_freeswitch_dir + "conf/"
	fs_dialplan_dir = fs_conf_dir + "dialplan/"
	fs_mod_dir	= g_global.tmp_freeswitch_dir + "mod/"

	os.makedirs(g_global.tmp_work_dir)
	os.makedirs(g_global.tmp_freeswitch_dir)
	os.makedirs(g_global.tmp_install_dir)
	os.makedirs(g_global.tmp_third_libs_dir)
	os.makedirs(g_global.tmp_system_files_dir)

	os.makedirs(fs_conf_dir)
	os.makedirs(fs_dialplan_dir)
	os.makedirs(fs_mod_dir)

	# 拷贝模块文件
	for mod_dir in g_global.load_libs.keys():
		mod_path = g_global.mod_dir + mod_dir + "/.libs/"
		for lib_name in  g_global.load_libs[mod_dir]:
			la_file = mod_path + lib_name + ".la"
			so_file = mod_path + lib_name + ".so"
			shutil.copy(la_file, fs_mod_dir)
			shutil.copy(so_file, fs_mod_dir)

	# 拷贝文件列表
	for file_array in g_global.copy_file_list:
		src = file_array[0]
		des = file_array[1]
		des_dir = des[0:des.rfind('/')]

		if not os.path.exists(des_dir):
			os.makedirs(des_dir)

		if os.path.isfile(src):
			shutil.copy(src, des)
		elif os.path.isdir(src):
			shutil.copytree(src, des)
		else:
			print(color_str(src + " not found", "red"))
			return False

	# update_docker.sh copy到install
	if not os.path.exists(g_global.update_sh_file_src):
		print(color_str(g_global.update_sh_file_src + " not found", "red"))
		return False
	else:
		shutil.copy(g_global.update_sh_file_src, g_global.update_sh_file_des_path)

	return True

# 1 写 模块加载文件 module.conf.xml as.conf.xml 列表到文件 module_load_conf
# 2 写 三方的安装参数到 文件 third_lib_install_param_file

def write_update_param():

	f = open(g_global.tmp_work_dir + g_global.module_load_conf_file, "w")
	#print("g_global.modules_load_conf:", g_global.modules_load_conf)
	for str in g_global.modules_load_conf:
		f.write(str + "\n")
	f.close

	f = open(g_global.tmp_work_dir + g_global.third_lib_install_param_file, "w")
	#print("g_global.install_param_list:", g_global.install_param_list)
	for str in g_global.install_param_list:
		f.write(str + "\n")
	f.close

	return True

def tar_update_file():
	tar_file = "docker_update.tar.gz"
	if 0 != os.system("cd " + g_global.tmp_work_dir + " ; tar -zcf " + tar_file + " ./*"):
		print(color_str("tar '" + tar_file + "' failed", "red"))
		return False
	else:
		print(color_str("generating '" + tar_file + "'", "sky_blue"))
	return True


def docker_build():

	if os.path.exists(g_global.dockerfile_sample_file):
		with open(g_global.dockerfile_sample_file, 'r') as f:
			sample_dockerfile_content = f.read()
		dockerfile_content = sample_dockerfile_content.replace('<BASEIMAGE>', g_global.base_image_name)

		with open(g_global.dockerfile_file, 'w') as f:
			f.write(dockerfile_content)

		dokcer_image_name =  g_global.image_name + ":" + g_global.image_tag
		docker_tar_name = g_global.image_name.split("/")[-1] + "_" + g_global.image_tag + ".tar"
		docker_tar_gz_name = docker_tar_name + ".gz"
		# 构建docker
		if 0 != os.system("docker build -f " + g_global.dockerfile_file + " -t " + dokcer_image_name + " " + g_global.tmp_work_dir):
			print(color_str("docker build failed", "red"))
			return False

		# 上传docker镜像到私有库
		#if 0 != os.system("docker push " + dokcer_image_name):
		#	print(color_str("docker push failed", "red"))
		#	#return False

		# 打包 docker镜像
		if 0 != os.system("docker save --output " + docker_tar_name + " " + dokcer_image_name):
			print(color_str("docker save failed", "red"))

		# 压缩镜像
		if 0 != os.system("tar -zcf " + docker_tar_gz_name + " " + docker_tar_name + " && rm -f " + docker_tar_name):
			print(color_str("tar '" + docker_tar_gz_name + "' failed", "red"))
			return False

		# 将本地的镜像删除
	#	os.system("docker image rm " + dokcer_image_name)
	else:
		print(color_str(g_global.dockerfile_sample_file + " file not found", "red"))
		return False
	return True

if __name__ == '__main__':
	ret = 0
	while True:	# 不是循环，只运行一次
		if len(sys.argv) <=1:
			print(color_str("input param error!", "red"))
			print("format: python docker_compile configure/XXX.yaml")
			ret = 1
			break

		# 根据yaml初始化全局变量
		if not yaml_conf_ini(sys.argv[1]):
			print(color_str("yaml_conf_ini error!", "red"))
			ret = 1
			break

		# 编译模块
		if not compile_modules():
			print(color_str("compile compile_modules failed", "red"))
			ret = 1
			break

		# 拷贝文件列表需要移动的文件
		if not copy_file():
			print(color_str("copy_file failed", "red"))
			ret = 1
			break

		# 写更新freeswitch 的参数文件
		if not write_update_param():
			print(color_str("write_update_param failed", "red"))
			ret = 1
			break

		# 打包 docker需要的更新文件
		if not tar_update_file():
			print(color_str("tar_update_file failed", "red"))
			ret = 1
			break

		# 构造docker
		if not docker_build():
			print(color_str("docker_build failed", "red"))
			ret = 1
			break

		print(color_str("compile success", "green"))
		ret = 0
		break

	# 将临时目录删除
	isExists=os.path.exists(g_global.tmp_work_dir)
	if isExists:
		os.system("rm " + g_global.tmp_work_dir + " -rf")
	exit(ret)
