# Toolbox testing guide

## Before You Run It

### Requirements

* RHEL 7/8 machine
* docker/podman installed on RHEL machine
* sshd installed and configured on RHEL machine
* Toolbox image pulled on RHEL machine
* two 3scale tenants and related access tokens

### Configuration

Extra configuration option for Toolbox tests is needed. This is example of configuration:

```yaml
toolbox:
  toolbox:
    cmd: "podman"
    podman_image: "" # hash of Toolbox image from `podman image list`
    destination_endpoint: "" # url to 3scale API endpoint of second tenant
    destination_provider_key: "" # access token for `destination_endpoint`
    machine_ip: "" # RHEL machine IP
    ssh_user: "" # SSH user for access to RHEL machine who is able to run podman images
    ssh_passwd: "" # SSH password of `ssh_user`

  threescale:
    version: "" # tested 3scale version, i.e. "2.11"
    admin:
      url: "" # url to 3scale API endpoint of first tenant
      token: "" # access token for `url`
```
`threescale` section is not usually needed because it is autoconfigured based on configuration of deployment in Openshift.

There are default options:
```
  toolbox:
    cmd: "podman" # method to run Toolbox via Podman. Other supported options are 'rpm' - Toolbox installed from RPM package, 'gem' - Toolbox install via Ruby Gem
    podman_cert_dir: "/var/data" # shared directory for storing temporary files(write permission needed). It can/should contain other files like certificate bundle.
    podman_cert_name: "ca-bundle.crt" # Certificate bundle to verify TLS connections. This can be disabled by configuration option 'ssl_verify: false'.
```

## Run Toolbox tests

There is an extra parameter required for Toolbox tests - `--toolbox`
Example:

```sh
make toolbox
```

[Run Toolbox tests via podman/docker](/README.md#run-the-tests-in-container)
