import fabric
from fabric.api import *
from fabtools import require
import fabtools
from fabtools.files import watch
from fabtools.require.python import virtualenv
import time
from fabtools.vagrant import vagrant
from fabric.contrib.files import upload_template, exists, sed, append, contains

env.is_jenkins_secure = True
env.jenkins_port = "8080"
env.jenkins_port_https = "8081"

env.jenkins_root_user = "jenkins_user"
env.jenkins_root_password = "SomeStrongPassword"

env.jenkins_cert_name = "ab_server"
env.jenkins_jobs = ['reactjs-job.yaml']


@task
def prod():
    env.settings = 'production'
    env.user = "root"
    env.hosts = ['']
    env.jenkins_jobs = ['']


def install_package_from_git(git_url, folder_name):
    if not exists(folder_name):
        run("git clone " + git_url)

    with cd(folder_name):
        sudo("sudo python setup.py install")


def install_python_packages():
    sudo("easy_install --upgrade pip")

    put("requirements.txt", "requirements.txt")
    fabtools.require.python.requirements('requirements.txt',
                                         use_sudo=True,
                                         user="root",
                                         download_cache="/opt/scb/rope/venv_cache")

    # Following packages are not in the pip now:
    install_package_from_git("https://github.com/openstack-infra/jenkins-job-builder.git", "jenkins-job-builder")
    install_package_from_git("https://github.com/lhupfeldt/jenkinsflow.git", "jenkinsflow")


def setup_jenkins_job(job_yaml):
    put("etc/" + job_yaml, job_yaml)
    run("jenkins-jobs --conf jenkins-jobs.ini update " + job_yaml)


@task
def setup_jenkins_jobs():
    upload_template("etc/jenkins-jobs-localhost.ini",
                    "jenkins-jobs.ini",
                    context=env,
                    use_sudo=False)

    for job_yaml in env.jenkins_jobs:
        setup_jenkins_job(job_yaml)


@task
def copy_ssh_keys():

    if not exists('/root/.ssh'):
        sudo('mkdir /root/.ssh')

    put("etc/id_rsa", "/root/.ssh/id_rsa", use_sudo=True)
    put("etc/id_rsa.pub", "/root/.ssh/id_rsa.pub", use_sudo=True)


def configure_jenkins():
    if not exists('/etc/jenkins'):
        sudo('mkdir /etc/jenkins')
    if not exists('/etc/jenkins/ssl'):
        sudo('mkdir /etc/jenkins/ssl')

    put("etc/%s.crt" % env.jenkins_cert_name,
        "/etc/jenkins/ssl/%s.crt" % env.jenkins_cert_name,
        use_sudo=True)

    put("etc/%s.key" % env.jenkins_cert_name,
        "/etc/jenkins/ssl/%s.key" % env.jenkins_cert_name,
        use_sudo=True)

    # Install git plugin
    #run("wget http://localhost:8080/jnlpJars/jenkins-cli.jar")
    put("etc/jenkins-cli.jar", "jenkins-cli.jar")

    # From https://gist.github.com/rowan-m/1026918
    run("wget -O default.js http://updates.jenkins-ci.org/update-center.json")
    run("sed '1d;$d' default.js > default.json")
    run('curl -X POST -H "Accept: application/json" -d @default.json http://localhost:8080/updateCenter/byId/default/postBack --verbose')

    run("java -jar jenkins-cli.jar -s http://localhost:%s/ install-plugin Git" % env.jenkins_port)

    # Required to make jenkins secure
    if env.is_jenkins_secure:
        put("etc/config.xml", "/var/lib/jenkins/config.xml", use_sudo=True)

    # TODO Make it run not from root
    upload_template("etc/jenkins",
                    "/etc/default/jenkins",
                    context=env,
                    use_sudo=True)

    # copy_ssh_keys()

    service("jenkins", "restart")


@task
def setup_www():
    require.nginx.server()


@task
def setup():

    # Change timezone
    sudo('echo "Asia/Singapore" > /etc/timezone')
    sudo('dpkg-reconfigure -f noninteractive tzdata')

    # Download 3rd party APT public key
    if not exists('jenkins-ci.org.key'):
        run('wget http://pkg.jenkins-ci.org/debian/jenkins-ci.org.key')

    # Tell APT to trust that key
    fabtools.deb.add_apt_key('jenkins-ci.org.key')
    require.deb.source('jenkins', 'http://pkg.jenkins-ci.org/debian', 'binary/')
    sudo("apt-get update")

    require.user(env.jenkins_root_user, password=env.jenkins_root_password)

    # Require some Debian/Ubuntu packages
    require.deb.packages([
        'mc',
        'vim',
        'python-virtualenv',
        'python-dev',
        'python-setuptools',
        'curl',
        'jenkins',
        'git',
        'ttf-dejavu',
        'python-software-properties',
        'software-properties-common',
        'ruby1.9.1'
    ])

    install_python_packages()

    configure_jenkins()

    setup_npm()
    setup_headless_browsers()
    setup_jenkins_jobs()

    setup_www()


@task
def setup_npm():
    require.deb.packages([

    ])

    sudo("add-apt-repository -y ppa:chris-lea/node.js")
    sudo("apt-get update")
    sudo("apt-get install -y nodejs")
    sudo("npm install -g grunt-cli")
    sudo("gem install compass")


@task
def setup_headless_browsers():

    # From http://alex.nederlof.com/blog/2012/11/19/installing-selenium-with-jenkins-on-ubuntu/
    sudo("""wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -""")
    sudo("""sudo sh -c 'echo deb http://dl.google.com/linux/chrome/deb/ stable main > /etc/apt/sources.list.d/google.list'""")

    sudo("apt-get update && sudo apt-get install -y xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic xvfb x11-apps  imagemagick firefox google-chrome-stable")
    put("etc/xvfb", "/etc/init.d/xvfb", use_sudo=True)
    sudo("chmod +x /etc/init.d/xvfb")
    sudo("update-rc.d xvfb defaults")


def service(name, *actions):
    """ Generic service function """
    for action in actions:
        sudo('service %s %s' % (name, action))


