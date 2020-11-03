# Performance tests

Performance tests are highly dependent on the creation of 3scale objects + the setup necessary things on openshift.


## How does it work?
For performance measurement, we are using [Hyperfoil](https://hyperfoil.io/). 
Hyperfoil is a microservice-oriented distributed benchmark framework.

The performance test consists of two files:

* `.hf.yaml` contains the performance test (benchmark), which will be executed on the hyperfoil.

* `test_.py` Test consist of the following phases:
    * **SETUP:** Test creates 3scale objects, configure openshift, and adds necessary configuration to the benchmark template (`.hf.yaml` file).
    * **RUN:** Test runs the created hyperfoil benchmark, and it waits for it to finish.
    * **ASSERT:** Test gathers results from hyperfoil and asserts if the run was successful and met the required threshold.
 
 
## How to run?
To run the performance tests, you need to setup hyperfoil first.
The testsuite needs to have a hyperfoil controller accessible with URL and the configuration for agents.
Testsuites `setting.yaml` contains predefined settings for clustered hyperfoil.

### Configuration
 ```yaml
hyperfoil:
  url: "http://hyperfoil-<URL>.com"
  shared_template:
```
Content of`shared_template` will be merged into each benchmark YAML definition.

* #### **Clustered hyperfoil**
     The easiest way how to run performance tests is to use clustered hyperfoil.
     
     Deploy by the [operator](https://hyperfoil.io/userguide/installation/k8s.html) or
     [manually](https://hyperfoil.io/userguide/installation/k8s_manual.html).
     
     Testsuite needs the following configuration:
     
     ```yaml
    hyperfoil:
      url: "http://hyperfoil-<URL>.com"
      shared_template:
        agents:
          agent-one:
    ```
    This is the minimum configuration needed to run smoke tests.

* #### **Manually deployed hyperfoil**
      Right now, we focus on running the testsuite with clustered hyperfoil. 
      There might be some difficulties with manually deployed hyperfoil.

    Hyperfoil can be deployed [manually](https://hyperfoil.io/userguide/installation/start_manual.html)
    or via [Ansible](https://hyperfoil.io/userguide/installation/ansible.html).

    Testsuite needs to have the following configuration:
     ```yaml
    hyperfoil:
      url: "http://hyperfoil-<URL>.com"
      shared_template:
        agents: 
    ```
    You need to fill it with your agent configuration.

### Running smoke tests
Smoke tests are used as examples of how to write performance tests and default tests that will check your configuration of hyperfoil.

When you configured hyperfoil, you need to configure the testsuite. Steps can be found in the root README file.

**WARNING**

You are running the performance tests, which can generate multiple requests per second.
Keep in mind that you need to choose your own backend. Otherwise, your actions can be considered as a DDoS attack.

Performance tests are only using the primary backend.
    
```yaml
threescale:
  service:
    backends:
      primary: http://httpbin.httpbin.svc:8080
``` 

The smoke tests can be run with the following command.
```shell script
make performance-smoke
```


## How to write a performance test?
**TBD**