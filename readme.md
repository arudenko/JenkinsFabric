# Configure Jenkins Instance with Fabric


This shows how to create simple Jenkins instance. This instance will have:

- Ubuntu
- Secured Jenkins with Git plugin
- Node/npm for JS packages
- [Karma](http://karma-runner.github.io/) as a runner for Unit Tests:
    `npm install -g karma`
- [Jasmine](http://pivotal.github.io/jasmine/) as Unit Test framework
- [Grunt](http://gruntjs.com/) as build tool
- Nginx to run static website 
- Selenium Framework ([WTFramework](https://github.com/wiredrive/wtframework))
- Headless Chrome and Firefox for functional tests
- Virtual display
- Pre-configured job to build and test project from [https://github.com/arudenko/ReactjsUnitTest](https://github.com/arudenko/ReactjsUnitTest)
    - checkout source code
    - build single page application
    - run Jasmine unit tests
    - deploy to local Nginx
    - run Selenium tests. If failed -- take a screenshot and attach to build


This setup works perfectly on small instance on [DigitalOcean](https://www.digitalocean.com/?refcode=8e25ea701943)


## Requirements

1. [Vagrant](http://www.vagrantup.com)
2. Python packages:
    - fabric
    - fabtools

## Run

`vagrant up && fab vagrant setup`

Open [http://88.88.88.88:8080/](http://88.88.88.88:8080/) in browser

Login: jenkins_user

Password: SomeStrongPassword


## References:

### Job Builder

To define jobs as YAML file:
[http://ci.openstack.org/jenkins-job-builder/](http://ci.openstack.org/jenkins-job-builder/)
[https://github.com/openstack-infra/jenkins-job-builder](https://github.com/openstack-infra/jenkins-job-builder)

### Jenkins Flow
To orchestrate Jenkins jobs through puthon file:

[https://github.com/lhupfeldt/jenkinsflow](https://github.com/lhupfeldt/jenkinsflow)

