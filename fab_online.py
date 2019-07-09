# -*- coding:utf-8 -*-
"""
    1. 负责通过 fab 来管理所有的 线上的 medweb 主服务相关的工作
    2. 所有的服务都以 online_ 开头。
    3. 该脚本在中控机上调用，相关的域名参考:
       http://git.chunyu.mobi/op/log_utils/blob/zhongkong/hosts
"""

import os
from fab_service.common import MEDWEB_DEPLOY_USER, check_commit_id, print_step_info, restart_supervisor,\
    DEFAULT_MEDWEB_PATH
from fabric.api import local, settings, cd, sudo, hosts, execute, run



def _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=None, restart_service=True):
    """
        线上服务，管理员(root)登陆，且以 chunyu 账号来执行

        @param code_dir:
        @param replace_settings:
        @param settings_name:
        @param do_compressor:
        @param commit_id: 例如: 38a03fcd59a191b3a26bce48912af22ba8e4e792 or master or develop
     """
    user = MEDWEB_DEPLOY_USER
    current_step_num = 0
    steps_num = 6 if restart_service else 5
    
    check_commit_id(commit_id)
    with cd(code_dir):
        # 更新代码
        # sudo("chown -R chunyu:chunyu *")
        # 10.2.15.35:/usr/local/data_do_not_delete/ 1913353216 1099045888 717114368  61% /home/chunyu/workspace/medweb/media/apk
        sudo("find . -path ./media -prune -o -print0 | xargs -0 chown chunyu:chunyu")
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "更新文件的owner")

        # 坚决杜绝任何形式的本地文件修改，添加等操作; 否则后果自负
        # 删除本地修改(但是不在版本库中就无能为力了)
        sudo("git reset --hard", user=user)
        sudo("find . -type f -name '*.pyc' -exec rm -fr '{}' \;")
        sudo("git clean -fd --exclude static --exclude cy_migrations --exclude log --exclude  templates")

        # git更新代码时出现问题，删除无效的branch
        sudo("git remote prune origin", user=user)
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "删除本地修改")

        # 更新代码
        sudo("git fetch origin", user=user)
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "更新代码")

        # checkout到指定的分支
        sudo("git checkout %s" % commit_id, user=user)
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "切换到指定分支")

        # 删除*.pyc文件
        sudo("find . -type f -name '*.pyc' -exec rm -fr '{}' \;")
        # 删除版本库之外的文件(.gitignore中的不管, 因此配置文件不会有问题)
        # 删除本地的目录文件
        # git clean -fdn --exclude static --exclude cy_migrations --exclude log --exclude  templates
        sudo("git clean -fd --exclude static --exclude cy_migrations --exclude log --exclude  templates")


        # 更新settings.py
        sudo('cp %s settings.py' % settings_name, user=user)
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "更新settings: %s" % settings_name)

        # 处理静态文件
        _do_rename_static_files() # 重命名静态文件及html内的相关引用，解决又拍云缓存不更新问题
        _do_collect_static()
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "处理静态文件")


        # 重启服务
        if restart_service:
            sudo('sh scripts/uwsgi/restart.sh', user=user)
            current_step_num += 1
            print_step_info(steps_num, current_step_num, "重启medweb")

def _do_rename_static_files():
    """
    # 服务器上需要安装以下环境：(如果服务器未安装gulp，则默认跳过此任务)
    # 1. 安装node `sudo apt-get install node`
    # 2. 安装gulp（全局和本地） `cd ~/repo/chunyu_admin/_frontend && sudo npm install gulp && sudo npm install -g gulp`
    # 3. 安装依赖包(安装时间较长，请耐心等待) `cd ~/repo/chunyu_admin/_frontend && sudo npm --registry "https://registry.npm.taobao.org" install `
    """
    run("echo '【重命名_frontend下的静态文件】'")
    run("hash gulp 2>/dev/null && cd _gearoll/ && gulp --app xxxx build:cache && cd ../  ||  echo >&2 'gulp未安装，重命名静态文件任务跳过'")
    run("echo '【重命名_frontend下的静态文件 DONE】'")


def _do_collect_static():
    with settings(warn_only=True):
        run('./PYTHON.sh manage.py collectstatic --noinput')

@hosts('root@md1')
def online_deploy_medweb1(commit_id):
    """
    部署线上md1服务器
    :param commit_id:
    """
    check_commit_id(commit_id)
    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.m123.py'

    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file)

    # 重启supervisor服务
    supervisor_path = os.path.join(DEFAULT_MEDWEB_PATH, "conf/supervisor/md1.supervisord.conf")
    supervisor_path_dest = os.path.join(DEFAULT_MEDWEB_PATH, "supervisord.conf")
    run('cp %s %s' % (supervisor_path, supervisor_path_dest))

    # restart_supervisor(supervisor_path_dest) 取消自动重启，改为运维操作


@hosts('root@md2', 'root@md3')
def online_deploy_medweb23(commit_id):
    """
        部署线上"RW"服务器, 数据库升级和服务器上线独立
        @param commit_id:
    """
    check_commit_id(commit_id)
    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.m123.py'

    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file)


@hosts('root@md4')
def online_deploy_medweb4(commit_id):
    """
        部署"计步器"服务器
        @param revision:
    """
    check_commit_id(commit_id)
    # 1. 更新medweb的代码
    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.m123.py'

    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file)


    # 2. 更新supervisor的脚本，并重启supervisor服务
    supervisor_path = os.path.join(DEFAULT_MEDWEB_PATH, "conf/supervisor/md4.supervisord.conf")
    supervisor_path_dest = os.path.join(DEFAULT_MEDWEB_PATH, "supervisord.conf")
    run('cp %s %s' % (supervisor_path, supervisor_path_dest))

    restart_supervisor(supervisor_path_dest)


@hosts('root@md6')
def online_deploy_medweb6(commit_id):
    '''
        部署对外服务的"只读服务器"
        @param revision:
    '''
    check_commit_id(commit_id)
    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.m6.py'

    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file)


    # 用于后台Admin处理的
    code_dir = "/home/chunyu/workspace/medweb_admin/"
    settings_file = 'settings.m123.py'
    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file)


@hosts('root@nginx2', 'root@nginx1')
def online_deploy_nginx2_https_res(commit_id):
    """
        部署https服务所需要的静态资源
        ./FAB.sh online_deploy_nginx2_https_res:commit_id=xxx

        1. 更新代码
        2. 使用只读的settings.py
        3. 本地图片的collect_static(https不能使用upyun的路径，除非upyun支持https协议)
    """
    check_commit_id(commit_id)

    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.m6.py'

    # 只部署资源，不重启服务
    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file, restart_service = False)

    with cd(DEFAULT_MEDWEB_PATH):
        with settings(warn_only=True):
            sudo('./PYTHON.sh manage.py collectstatic --noinput', user=MEDWEB_DEPLOY_USER)


# @hosts('root@summer2')
# def online_deploy_summer2_backup(commit_id):
#     check_commit_id(commit_id)
#
#     code_dir = DEFAULT_MEDWEB_PATH
#     settings_file = 'settings.backup.py'
#
#     # 只部署资源，不重启服务
#     _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file, restart_service = True)

@hosts('root@jan2')
def online_deploy_jan2(commit_id):
    check_commit_id(commit_id)

    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.jan2.py' # 只读服务器

    # 只部署资源，不重启服务
    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file, restart_service = False)

# @hosts('root@mar2')
# def online_deploy__mar2(commit_id):
#     check_commit_id(commit_id)
#
#     code_dir = DEFAULT_MEDWEB_PATH
#     settings_file = 'settings.m6.py'
#
#     # 只部署资源，不重启服务
#     _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file, restart_service = False)

@hosts('root@jan1')
def online_deploy_jan1(commit_id):
    check_commit_id(commit_id)

    code_dir = DEFAULT_MEDWEB_PATH
    settings_file = 'settings.jan1.py'

    # 只部署资源，不重启服务
    _deploy_with_root_and_chunyu(code_dir, commit_id, settings_name=settings_file, restart_service = False)

    # 2. 更新supervisor的脚本，并重启supervisor服务
    supervisor_path = os.path.join(DEFAULT_MEDWEB_PATH, "conf/supervisor/jan1.supervisord.conf")
    supervisor_path_dest = os.path.join(DEFAULT_MEDWEB_PATH, "supervisord.conf")
    run('cp %s %s' % (supervisor_path, supervisor_path_dest))

    restart_supervisor(supervisor_path_dest)


def online_deploy_all_medwebs(commit_id):
    """
        部署线上服务
            ./FAB.sh online_deploy_all_medwebs:commit_id=xx

        完成工作:
        1. 更新redis cache(通过一个进程加载数据, 避免一百多个进程在启动时同时读取数据库)
        2. md 1, 2,3 更新代码，并且重启服务(读写服务器)
        3. md 6 更新代码，重启服务器(只读)
        4. https服务器更新静态文件（不重启)

    """
    check_commit_id(commit_id)

    local('./PYTHON.sh manage.py cyexec reboot_precache precache_disease_manager')


    # 2. 部署medweb服务器
    execute(online_deploy_medweb1, commit_id)
    execute(online_deploy_medweb23, commit_id)
    execute(online_deploy_medweb6, commit_id)

    # 3. 更新https的静态资源
    #    nginx1, nginx2都有可能充当https服务器
    execute(online_deploy_nginx2_https_res, commit_id)

    # # 计步器:
    # execute(deploy_medweb4, commit_id)

    # 其他历史残留
    execute(online_deploy_jan2, commit_id)
    execute(online_deploy_jan1, commit_id)
