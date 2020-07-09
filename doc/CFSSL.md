## Getting cfssl up and running on your local machine for testsuite 

### Installing cfssl

Install cfssl on your local machine by following the instructions in the README at https://github.com/cloudflare/cfssl


### Certificate Authority

You need valid certificate authority which will be used by cfssl for signing certificates.

You can create self-signed ones using `openssl`:

```bash
openssl genrsa -out rootCA.key 2048
openssl req -batch -new -x509 -nodes -key rootCA.key -sha256 -days 1024 -out rootCA.pem
```

### Running cfssl server

To have cfssl server up and running somewehere, you can execute the following command:

```bash
cfssl serve -address 0.0.0.0 -port 8888 -ca /var/certs/rootCA.pem -ca-key /var/certs/rootCA.key
```

**OBS: Change the path of the CA key and pem with yours.**


### Updating settings.local.yaml

Update `config/settings.local.yml` file appending the following snippet to it:

```yaml
cfssl:
  host: 0.0.0.0 # CFSSL server api URL
  port: 8888    # CFSSL server api port
```
