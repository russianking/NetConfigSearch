# -*- coding: utf-8 -*-
import os,shutil
import zipfile,gzip,tarfile
import re
import chardet
import logger

is_open_file_twice = False
is_recurssively_decompress = True
exclude_path = ['lib']
exclude_files = ['.class','.dll','pom.','LICENSE','MANIFEST','NOTICE','log4j','Log4j','.svg','.txt','.xsd','.wsdl',
                 '.tld','.dtd','.types','DEPENDENCIES','lombok','.png','.gif','.js']
exclude_words = ['springframework','apache','javaee','LICENSE','log4j','github','GPL','atlassian',' licensing','sun.com','sap.']

def main():
    #file_path = sys.argv[1]
    tmpdir =  os.path.join(os.getcwd(),'envcheck_tmppath')
    file_path = input('请输入存放代码的目录：\n')
    if os.path.exists(file_path):
        log.info('创建临时文件目录{}...'.format(tmpdir))
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
        log.info('拷贝指定文件夹{}至临时文件目录...'.format(file_path))
        try:
            copy_dir(file_path,tmpdir) #拷贝文件夹至当前文件夹下的tmppath目录下
            log.info('解压临时文件目录{}...'.format(tmpdir))
            file_decompress(tmpdir)
            log.info('解压完成，正提取IP及URL...')
            file_check(tmpdir)
            #log.info('删除临时目录{}...\n'.format(tmpdir))
            log.info('\n'
                     '==========================================================\n'
                     '请在当前目录下的日志文件envcheck_out.log中检查提取的IP和域名\n'
                     '检查后请手工删除当前目录下的临时目录envcheck_tmppath\n'
                     '=========================================================='
                     .format(tmpdir))
        except Exception as e:
            log.error(e)
            input()
        # finally:
        #     shutil.rmtree(tmpdir)
    else:
        log.info('您的输入文件目录不存在')
    input()

def file_check(file_path):
    for root,dirs,files in os.walk(file_path):
        if is_excluded_path(root):
            continue
        for file in files:
            if is_excluded_file(file):
                continue
            file_path = os.path.join(root, file)
            try:
                list = detect_ip_url(file_path)
            except UnicodeDecodeError:
                log.info('文件{}存在编码问题，尝试检测编码后再次打开...'.format(file_path))
                try:
                    f1 = open(file_path,'rb')
                    firstline = f1.readline()
                    file_encoding = chardet.detect(firstline).get('encoding')
                    list = detect_ip_url(file_path,encode=file_encoding)
                except UnicodeDecodeError as e:
                    log.error('二次打开文件失败'+e.__str__())
                    continue
                finally:
                    f1.close()
            except Exception as e:
                log.error('文件打开异常...\n %s'%e)
                continue
            if len(list) > 0:
                log.info('文件{}的网络环境配置:'.format(file_path))
                for i in list:
                    log.info(i) #打印输出IP域名列表
            else:
                log.info('文件{}的网络环境配置:无'.format(file_path))

def find_ip_url(line):
    ip_pattern = re.search(r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
                           line,re.IGNORECASE)
    if ip_pattern:
        return line
    #url_pattern = re.search(r'(http|ftp|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?',line,re.IGNORECASE)
    #url_pattern = re.search(r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,62}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',line,re.IGNORECASE)
    #url_pattern = re.search(r'(?:[a-z0-9_](?:((?!,)[a-z0-9-_]){0,62}[a-z0-9])?\.){2,4}(?:([a-z](?<!\.)){2,6})', line,re.IGNORECASE)
    url_pattern = re.search(r'(?:[a-z0-9_](?:((?!,)[a-z0-9-_]){0,62}[a-z0-9])?\.){1,6}(?:(cn|com|net|org)\b)', line,
                            re.IGNORECASE)
    if url_pattern:
        for word in exclude_words:
            if word in line:
                return ''
        return line
    return ''

def detect_ip_url(file, encode = ''):
    list = []
    if encode == '':
        try:
            with open(file, 'r') as f:
                for line in f:
                    if len(find_ip_url(line.strip('\n'))) > 0:
                        list.append(line.strip('\n'))
        except UnicodeDecodeError:
            with open(file, 'r', encoding = 'utf-8') as f:
                for line in f:
                    if len(find_ip_url(line.strip('\n'))) > 0:
                        list.append(line.strip('\n'))
    else:
        with open(file, 'r', encoding=encode) as f:
            for line in f:
                if len(find_ip_url(line.strip('\n'))) > 0:
                    list.append(line.strip('\n'))
    return list

def file_decompress(file_path):
    for root, dirs, files in os.walk(file_path):
        if is_excluded_path(root):
            continue
        for file in files:
            try:
                file_type = os.path.splitext(file)[-1]
                file_name = os.path.join(root, file)
                unzip_path = file_name + "_files"
                if(file_type == '.jar' or file_type == '.zip'):
                    log.info('解压文件'+file_name)
                    zip_file = zipfile.ZipFile(file_name)
                    if not os.path.isdir(unzip_path):
                        os.mkdir(unzip_path)
                    for names in zip_file.namelist():
                        zip_file.extract(names, unzip_path)
                    zip_file.close()
                    os.remove(file_name)
                if(file_type == '.gz'):
                    log.info('解压文件' + file_name)
                    f_name = file_name.replace(".gz", "")
                    g_file = gzip.GzipFile(file_name)
                    open(f_name, "w+").write(g_file.read())# gzip对象用read()打开后，写入open()建立的文件里。
                    g_file.close()
                    os.remove(file_name)
                if(file_type == '.tar'):
                    log.info('解压文件' + file_name)
                    tar = tarfile.open(file_name)
                    names = tar.getnames()
                    if not os.path.isdir(unzip_path):
                        os.mkdir(unzip_path)# 因为解压后是很多文件，预先建立同名目录
                    for name in names:
                        tar.extract(name, unzip_path)
                    tar.close()
                    os.remove(file_name)
                if('.tar.gz' in file):
                    log.info('解压文件' + file_name)
                    f_name = file_name.replace(".gz", "")
                    unzip_path = f_name + '_files'
                    g_file = gzip.GzipFile(file_name)
                    open(f_name, "w+").write(g_file.read())  # gzip对象用read()打开后，写入open()建立的文件里。
                    g_file.close()
                    os.path.splitext(file)
                    tar = tarfile.open(f_name)
                    names = tar.getnames()
                    if not os.path.isdir(unzip_path):
                        os.mkdir(unzip_path)  # 因为解压后是很多文件，预先建立同名目录
                    for name in names:
                        tar.extract(name, unzip_path)
                    tar.close()
                    os.remove(file_name)
                if is_recurssively_decompress:
                    file_decompress(unzip_path) #对解压出来的目录进行递归解压
            except Exception as e:
                log.error(('解压文件{}异常'+e.__str__()).format(os.path.join(root,file)))
                continue

def copy_dir(path,outpath):
    for file in os.listdir(path):
        name = os.path.join(path, file)
        back_name = os.path.join(outpath, file)
        if os.path.isfile(name):
            shutil.copy(name, back_name)
        else:
            if not os.path.isdir(back_name):
                os.makedirs(back_name)
            copy_dir(name, back_name)

def is_excluded_file(file):
    for word in exclude_files:
        if word in file:
            return True

def is_excluded_path(path):
    for p in exclude_path:
        if p in path:
            return True

log = logger.Logger()

if(__name__ == '__main__'):
    main()