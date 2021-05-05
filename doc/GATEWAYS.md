# Known Capabilities
* `PRODUCTION_GATEWAY`: Gateway contains production gateway and can be used for calls to production. It needs to implement reload() method
* `APICAST`: Gateway is APIcast, mutually exclusive with `SERVICE_MESH`.
* `SERVICE_MESH`: Gateway is Service Mesh, mutually exclusive with `APICAST`. 
* `CUSTOM_ENVIRONMENT`: You can set or read environmental variables for gateway. It needs to implement environ() method
* `SAME_CLUSTER`: Gateway is always located on the same cluster as 3scale, so it has access to internal services.
* `STANDARD_GATEWAY`: Default gateway deployed by 3scale, which means tests that deploy their own APIcast can run.
* `LOGS`: Allows getting APIcast logs through `get_logs()` method
* `JAEGER`: Allows configuring the APIcast to send data to Jaeger through `connect_jaeger()` method


# Gateway type configuration
## System APIcast
*Description*: Default APIcasts that are deployed with 3scale.

*Capabilities*: "APICAST, CUSTOM_ENVIRONMENT, PRODUCTION_GATEWAY, SAME_CLUSTER, LOGS, JAEGER, STANDARD_GATEWAY" 
```
gateway:
  image: "my-apicast-image"                                                              # Optional: Custom image, it is not directly used by SystemAPIcast but it is used by all custom gateway tests
  template: "path/to/template or url"                                                    # Optional: Template, it is not directly used by SystemAPIcast but it is used by all custom gateway tests
  type: "apicast"
  configuration:
    staging_deployment: "apicast-staging"              # Name of the staging apicast deployment in the Openshift
    production_deployment: "apicast-production"        # Name of the production apicast deployment in the Openshift
```
## Self-managed APIcast
*Description*: Self-managed APIcast that is already deployed in the OpenShift.

*Capabilities*: "APICAST, CUSTOM_ENVIRONMENT, PRODUCTION_GATEWAY, LOGS, JAEGER" 
```
gateway:
  type: "apicast-selfmanaged"
  configuration:
    endpoints:
        sandbox: "http://%s-staging.localhost:8080"                 # Wildcard address for staging address for service
        production: "http://%s-production.localhost:8080"           # Wildcard address for production address for service
    deployment:                                                     # DeploymentConfigs
        staging: "selfmanaged-staging"
        production: "selfmanaged-production"
    project: "threescale"                                           # OpenShift project containing the apicasts
    server: "server"                                                # OpenShift server containing the apicasts
```
## Container APIcast
*Description*: Similar to Self-managed APIcast (at least for now), used for interop testing.
Expects gateway deployed remotely without any access to it.

*Capabilities*: "APICAST" 
```
gateway:
  type: "apicast-container"
  configuration:
    sandbox_endpoint: "http://%s-staging.localhost:8080"             # Wildcard address for staging address for service
    production_endpoint: "http://%s-production.localhost:8080"       # Wildcard address for production address for service
```
## Apicast Operator
*Description*: Self-managed APIcast deployed by the operator, requires project with deployed `APIcast Operator`.
 Testsuite will create APIcast CRDs. Can be run in parallel.

*Capabilities*: "APICAST, PRODUCTION_GATEWAY" 
```
gateway:
  type: "apicast-selfmanaged"
  configuration:
    endpoints:
        sandbox: "http://%s-staging.localhost:8080"                 # Wildcard address for staging address for service
        production: "http://%s-production.localhost:8080"           # Wildcard address for production address for service
    deployment:                                                     # Deployments names for the newly created apicasts
        staging: "apicast-staging"
        production: "apicast-production"
    project: "threescale"
    server: "server"                                
    randomized: False                                               # True, if endpoints and deployments should be blamed 
```
## Template APIcast
*Description*: Self-managed APIcast deployed by testsuite from template.
Used for self-managed APIcast testing on OpenShift 3.11.  Can be run in parallel.

*Capabilities*: "APICAST, CUSTOM_ENVIRONMENT, PRODUCTION_GATEWAY, SAME_CLUSTER, LOGS, JAEGER"
```
gateway:
  image: "my-apicast-image"                                                              # Optional: Custom image
  template: "path/to/template or url"                                                    # Optional: Template to be used
  type: "apicast-template"
  configuration:
    deployments:
        staging: "template-apicast-staging"                                              # Staging deployment name
        production: "template-apicast-production"                                        # Production deployment name
    endpoints:
        staging: "https://%s.localhost:8080"                                             # Optional: Wildcard address for staging address for service
        production: "https://%s.localhost:8080"                                          # Optional: Wildcard address for production address for service
    apicast_configuration_url: "https://<admin access token>@<3scale admin URL>"         # Optional: Apicast config. URL
    service_routes: True                                                                 # Optional: If Apicats should create automatic route for each service
    randomized: False                                                                    # True, if endpoints and deployments should be blamed 
```
## TLS APIcast
*Description*: Extension to Template APIcast, which sets up APIcast for TLS communication

*Capabilities*: "APICAST, CUSTOM_ENVIRONMENT, PRODUCTION_GATEWAY, SAME_CLUSTER, LOGS, JAEGER"
```
gateway:
  image: "my-apicast-image"                                                              # Optional: Custom image
  template: "path/to/template or url"                                                    # Optional: Template to be used
  type: "apicast-tls"
  configuration:
    deployments:
        staging: "tls-apicast-staging"                                                   # Staging deployment name
        production: "tls-apicast-production"                                             # Production deployment name
    endpoints:
        staging: "https://%s.localhost:8080"                                             # Optional: Wildcard address for staging address for service
        production: "https://%s.localhost:8080"                                          # Optional: Wildcard address for production address for service
    apicast_configuration_url: "https://<admin access token>@<3scale admin URL>"         # Optional: Apicast config. URL
    service_routes: True                                                                 # Optional: If Apicats should create automatic route for each service
    randomized: False                                                                    # True, if endpoints and deployments should be blamed 
```

## Service Mesh gateway
*Description*: Gateway for 3scale-istio-adapter with service mesh (Istio)

*Capabilities*: "ISTIO"
```
gateway:
  type: "service-mesh"
  configuration:
    projects:
        httpbin: "httpbin"               # Project where Httpbin will be deployed
        service_mesh: "service-mesh"     # Project with Service Mesh deployed
    server: "istio"                      # Openshift server with Service mesh
```

# Example configurations
## Changing Gateway image for custom gateway tests
Even though standard gateway (System APIcast) won't care about this image and template, tests using custom gateway, like TLS or parameters, will.
```
custom_image:
  threescale:
    gateway:
      image: "my-apicast-image"
      template: "path/to/template" 
```
## Self-managed APIcast tests on 3.11
Used for running Self-managed tests on OCP 3.11.
```
selfmanaged:
  threescale:
    gateway:
      type: "apicast-template"
      configuration:
        deployments:
          staging: "selfmanaged-staging"
          production: "selfmanaged-prod"
        randomize: true
```
### Self-managed APIcast tests on 3.11 with custom image and template
Used for running Self-managed tests on OCP 3.11, but with custom image and template.
Useful for testing configurations in release cycle, where you want to run this with image from errata and template from RPM.
```
selfmanaged:
  threescale:
    image: "my-apicast-image"
    template: "path/to/template" 
    gateway:
      type: "apicast-template"
      configuration:
        deployments:
          staging: "selfmanaged-staging"
          production: "selfmanaged-prod"
        randomize: true
```
## Self-managed APIcast tests on 4.x

### APIcast Operator deployed in the same project
```
selfmanaged:
  threescale:
    gateway:
      type: "apicast-operator"
      configuration:
        deployments:
          staging: "selfmanaged-staging"
          production: "selfmanaged-prod"
        randomize: true
```
### APIcast Operator deployed in different project
This is usually setup for testing self-managed APIcast on various configuration during release cycle.
You don't need to override image or template since you are always testing with images baked in the operator. 
```
selfmanaged:
  threescale:
    gateway:
      type: "apicast-operator"
      configuration:
        deployments:
          staging: "selfmanaged-staging"
          production: "selfmanaged-prod"
        randomize: true
        project: "apicast"
  openshift:
    projects:
      apicast:
        name: "apicast-operator"        
```

## Service Mesh
To run Service Mesh configurations, you need:
* Deployed Service Mesh in separate project (e.g. service-mesh) with configured adapter (Turned off SSL verify, changed policy and telemetry to Mixer).
* Project which is part of the mesh (ServiceMeshMember) and to which testsuite will deploy the Httpbins. It can be tools but might leave some trash behind.
### On the same cluster
```
selfmanaged:
  threescale:
    gateway:
      type: "service-mesh"
      configuration:
        projects:
          httpbin: "httpbin"
          mesh: "service-mesh"
  openshift:
    projects:
      service-mesh:
        name: "service-mesh"
      httpbin:
        name: "httpbin"
```

### On different cluster
You can leverage testsuite ability to use multiple cluster and run ServiceMesh on a different cluster than the 3scale you are testing it with.
Can be useful for testing with 3scale on 3.11, since ServiceMesh works only on OCP 4.
```
servicemesh:
  threescale:
    gateway:
      type: "service-mesh"
      configuration:
        projects:
          httpbin: "httpbin"
          mesh: "service-mesh"
        server: "mesh"
  openshift:
    projects:
      service-mesh:
        name: "service-mesh"
      httpbin:
        name: "httpbin"
    servers:
      mesh:
        server_url: "api_url:8443"
        token: "randomtokenstring"        
```