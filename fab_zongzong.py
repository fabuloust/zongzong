# -*- coding:utf-8 -*-
from fabric.api import settings, cd, run, hosts
from colorama import Fore

from settings import OWN_APPS

"""
fab 管理
"""


def print_step_info(total_step, current_step, msg):
    """
    显示部署的进度
    """
    print((Fore.MAGENTA + "进度: [%s/%s" + Fore.RESET + "] %s") % (current_step, total_step, msg))
    if total_step == current_step:
        print(Fore.GREEN + "完工" + Fore.RESET)

    print("")


def _test_do_rename_static_files():
    """
    # 服务器上需要安装以下环境：(如果服务器未安装gulp，则默认跳过此任务)
    # 1. 安装node `sudo apt-get install node`
    # 2. 安装gulp（全局和本地） `cd ~/repo/medweb/_frontend && sudo npm install gulp && sudo npm install -g gulp`
    # 3. 安装依赖包(安装时间较长，请耐心等待) `cd ~/repo/medweb/_frontend && sudo npm --registry "https://registry.npm.taobao.org" install `
    """
    run("echo '【重命名_frontend下的静态文件】'")
    run("hash gulp 2>/dev/null && cd _frontend/ && gulp build:html && cd ../  ||  echo >&2 'gulp未安装，重命名静态文件任务跳过'")
    run("echo '【重命名_frontend下的静态文件 DONE】'")


def _test_do_collect_static():
    with settings(warn_only=True):
        run('./PYTHON.sh manage.py collectstatic --noinput')


def _test_db_schema_migration():
    """
    对所有app进行makemigrations
    """
    run("./PYTHON.sh manage.py makemigrations {}".format(' '.join(OWN_APPS)))


def _test_db_migrate():
    """
    migrate
    """
    run("./PYTHON.sh manage.py migrate {}".format(' '.join(OWN_APPS)))


def test_db_migrate_all():
    """
    对所有的app进行migrate
    """
    run("./PYTHON.sh manage.py migrate --all")


def _test_deploy_with_user(code_dir, commit_id, settings_name=None, same_database=True):
    """
        以"当前用户"的身份
        @param code_dir:
        @param settings_name:
        @param commit_id: 例如: 38a03fcd59a191b3a26bce48912af22ba8e4e792 or master or develop
    """
    current_step_num = 0
    steps_num = 8

    with cd(code_dir):
        # 1. 将所有的本地修改直接revert
        run("git reset --hard")
        # run("find . -path ./media -prune -o -print0 | xargs -0 chown chunyu:chunyu")
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "删除本地修改")

        # 2. 更新代码
        run("git fetch origin")
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "更新代码")

        # 3. checkout到指定的分支，如果为master / develop 则为指定分支的最新代码
        run("git checkout %s" % commit_id)
        if commit_id == "master":
            run("git pull origin %s" % commit_id)
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "切换到指定分支")

        # 4.删除*.pyc文件
        run("find . -type f -name '*.pyc' -exec rm -fr '{}' \;")
        run("git clean -fd --exclude static --exclude cy_migrations --exclude log --exclude  templates")
        print_step_info(steps_num, current_step_num, "删除版本库之外的文件")

        # 5.更新settings.py
        # run('cp %s settings.py' % settings_name)
        # current_step_num += 1
        # print_step_info(steps_num, current_step_num, "更新settings")
        # run('source ../ENV/bin/activate')
        # run('pip install -r requirements.txt')

        # 6.处理静态文件
        _test_do_rename_static_files()  # 重命名静态文件及html内的相关引用，解决又拍云缓存不更新问题
        _test_do_collect_static()
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "处理静态文件")

        # 7.数据库的处理
        _test_db_schema_migration()
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "生成数据库的调整方案")

        _test_db_migrate()
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "执行数据库的升级")

        # 8. 重启服务
        run('sh scripts/uwsgi/restart.sh')
        current_step_num += 1
        print_step_info(steps_num, current_step_num, "重启服务")


@hosts('root@59.110.161.78:22')
def zongzong(commit_id='master'):
    """
        # ./FAB.sh biztest:commit_id=xxx
    fab zongzong
    """
    code_dir = "/root/workspace/zongzong"
    settings_file = "settings.py"

    # 1. 部署代码
    _test_deploy_with_user(code_dir, commit_id, settings_name=settings_file)

