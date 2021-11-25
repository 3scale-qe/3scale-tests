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
  default:
    kind: "SystemApicast"
```
## Container APIcast
*Description*: Similar to Self-managed APIcast (at least for now), used for interop testing.
Expects gateway deployed remotely without any access to it.

*Capabilities*: "APICAST" 
```
gateway:
  default:
    kind: "ContainerizedApicast"
    endpoint: "http://%s.localhost:8080"   # Wildcard url used for service endpoint
```
## APIcast Operator
*Description*: Self-managed APIcast deployed by the operator, requires project with deployed `APIcast Operator`.
 Testsuite will create APIcast CRDs. Can be run in parallel.

*Capabilities*: "APICAST, PRODUCTION_GATEWAY" 
```
gateway:
 default:
   openshift:                            # Optional: Configuration of OpenShiftClient
     project_name: "apicast-operator"    # Optional: project with the operator
     server_url: "https://api.oc.net"    # Optional: server url of the API server
     token: "abcdef"                     # Optional: token for that Openshift server
     kind: "OpenShiftClient"
   name: "gateway-test"                  # Name for the APIcast resource
   generate_name: true                   # True, if the name should have a random suffix
   kind: "OperatorApicast"
```
## Template APIcast
*Description*: Self-managed APIcast deployed by testsuite from template.
Used for self-managed APIcast testing on OpenShift 3.11.  Can be run in parallel.

*Capabilities*: "APICAST, CUSTOM_ENVIRONMENT, PRODUCTION_GATEWAY, SAME_CLUSTER, LOGS, JAEGER"
```
gateway:
 default:
   openshift:                            # Optional: Configuration of OpenShiftClient
     project_name: "apicast-operator"    # Optional: project with the operator
     server_url: "https://api.oc.net"    # Optional: server url of the API server
     token: "abcdef"                     # Optional: token for that Openshift server
     kind: "OpenShiftClient"
   name: "gateway-test"                  # Name for the APIcast resources
   generate_name: true                   # True, if the name should have a random suffix
   template: "<template_url_or_path>"    # Template for deployment
   image: "<image>                       # Optional: Image to be used
   path_routing: false                   # Optional: True, if the path_routing should be used
   kind: "TemplateApicast"
```
## TLS APIcast
*Description*: Extension to Template APIcast, which sets up APIcast for TLS communication

*Capabilities*: "APICAST, CUSTOM_ENVIRONMENT, PRODUCTION_GATEWAY, SAME_CLUSTER, LOGS, JAEGER"
```
gateway:
 default:
   openshift:                            # Optional: Configuration of OpenShiftClient
     project_name: "apicast-operator"    # Optional: project with the operator
     server_url: "https://api.oc.net"    # Optional: server url of the API server
     token: "abcdef"                     # Optional: token for that Openshift server
     kind: "OpenShiftClient"
   name: "gateway-test"                  # Name for the APIcast resources
   generate_name: true                   # True, if the name should have a random suffix
   template: "<template_url_or_path>"    # Template for deployment
   image: "<image>                       # Optional: Image to be used
   path_routing: false                   # Optional: True, if the path_routing should be used
   kind: "TemplateApicast"
```

## Service Mesh gateway
*Description*: Gateway for 3scale-istio-adapter with service mesh (Istio)

*Capabilities*: "ISTIO"
```
gateway:
  default:
    kind: "ServiceMeshGateway"
    httpbin:                             # OpenShiftClient used for all httpbins
      project_name: "httpbin"
      kind: "OpenShiftClient"
    mesh:                                # OpenShiftClient where Service Mesh is installed, both httpbin and Service Mesh must be on the same server
      project_name: "service-mesh"       
      kind: "OpenShiftClient"
```

# Gateways for custom gateway tests
You can include additional configuration for custom gateways by including a section with the gateway name like this
You can find all configuration options in a section related to the chosen gateway.
```
gateway:
  TemplateApicast:
    template: apicast.yml               # Template that will be only used in tests using TemplateApicast
  default:
    kind: "SystemApicast"
```
# Example configurations
## Changing Gateway image for custom gateway tests
Even though standard gateway (System APIcast) won't care about this image and template, tests using custom gateway, like TLS or parameters, will.
```
gateway:
  TemplateApicast:
    template: apicast.yml               # Template that will be only used in tests using TemplateApicast
    image: "<image>"
```
## Self-managed APIcast tests on 3.11
Used for running Self-managed tests on OCP 3.11.
```
selfmanaged:
  threescale:
   gateway:
    default:
      name: "selfmanaged"
      generate_name: true
      template: "<template_url_or_path>" 
      kind: "TemplateApicast"
```
### Self-managed APIcast tests on 3.11 with custom image and template
Used for running Self-managed tests on OCP 3.11, but with custom image and template.
Useful for testing configurations in release cycle, where you want to run this with image from errata and template from RPM.
```
selfmanaged:
  threescale:
   gateway:
    default:
      name: "selfmanaged"
      generate_name: true
      template: "<template_url_or_path>"
      image: "<image>"
      kind: "TemplateApicast"
```
## Self-managed APIcast tests on 4.x

### APIcast Operator deployed in the same project
```
selfmanaged:
  threescale:
   gateway:
    default:
      name: "selfmanaged"
      generate_name: true
      kind: "OperatorApicast"
```
### APIcast Operator deployed in different project
This is usually setup for testing self-managed APIcast on various configuration during release cycle.
You don't need to override image or template since you are always testing with images baked in the operator. 
```
selfmanaged:
  threescale:
   gateway:
    default:
     openshift:
       project_name: "apicast-operator"
       kind: "OpenShiftClient"
      name: "selfmanaged"
      generate_name: true
      kind: "OperatorApicast"   
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
     default:
       kind: "ServiceMeshGateway"
       httpbin:
         project_name: "httpbin"
         kind: "OpenShiftClient"
       mesh:
         project_name: "service-mesh"
         kind: "OpenShiftClient"
```

### On different cluster
You can leverage testsuite ability to use multiple cluster and run ServiceMesh on a different cluster than the 3scale you are testing it with.
Can be useful for testing with 3scale on 3.11, since ServiceMesh works only on OCP 4.
```
servicemesh:
  threescale:
   gateway:
     default:
       kind: "ServiceMeshGateway"
       httpbin:                             # OpenShiftClient used for all httpbins
         project_name: "httpbin"
         server_url: "<url>"
         token: "<token>"
         kind: "OpenShiftClient"
       mesh:                                # OpenShiftClient where Service Mesh is installed, both httpbin and Service Mesh must be on the same server
         project_name: "service-mesh"
         server_url: "<url>"
         token: "<token>"  
         kind: "OpenShiftClient"   
```