# CFMapserver

CFMapserver is a wrapper utility for deploying [MapServer](https://mapserver.org/about.html#aboutMapServer) on Kubernetes, and enabling automated updates of mapfiles.

## How it works

CFMapserver is available as a [Helm](https://helm.sh/) chart, which enables deploying MapServer instances on Kubernetes fast, with minimum configuration.
MapServer gets deployed as a container and serves map files from /etc/mapserver folder. The contents of this folder are by default populated based on the contents of your S3 bucket. 
If the map files in the buckets change (e.g. are added, deleted or updated), a Kubernetes cronjob will periodically update the /etc/mapserver contents as well.

## Prerequisites
* A running Kubernetes cluster (e.g. on CloudFerro WAW3-1 cloud, with integrated EO data repository) -> [CloudFerro Kubernetes on Magnum installation guide](https://creodias.docs.cloudferro.com/en/latest/kubernetes/How-to-Create-a-Kubernetes-Cluster-Using-Creodias-OpenStack-Magnum.html)
* kubectl installed -> [Install kubectl on Linux](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
* Helm installed -> [Installing Helm](https://helm.sh/docs/intro/install/)
* S3 credentials to mapfiles bucket -> [CloudFerro guideline, EC2 keys generation](https://creodias.docs.cloudferro.com/en/latest/general/How-to-generate-ec2-credentials-on-Creodias.html?highlight=generate%20s3)


## Configuring the chart

The following table lists the configurable parameters of the template Helm chart and their default values.

| Parameter                  | Description                                     | Default                                                    |
| -----------------------    | ---------------------------------------------   | ---------------------------------------------------------- |
| `s3Maps.host`        | S3 endpoint URL for storing map files                                 | `https://s3.waw3-1.cloudferro.com`                         |
| `s3Maps.bucket`      | S3 bucket for map files (please store mapfiles directly in this S3 bucket, use of folders is currently not supported with the default setup)        | ``     |
| `s3Maps.accessKey`  | S3 access key for map files                                 | ``                                                         |
| `s3Maps.secretKey`    | S3 secret key for map files                                  | ``                                                         |
| `s3Geo.host`        | S3 endpoint URL for geo images                                 | `https://s3.waw3-1.cloudferro.com`                         |
| `s3Geo.bucket`      | S3 bucket for geo images        | ``     |
| `s3Geo.accessKey`  | S3 access key for geo images                               | ``                                                         |
| `s3Geo.secretKey`    | S3 secret key for geo images                                  | ``                                                         |
| `cronJobSchedule`          | Synchronization schedule between S3 bucket and map files path, in cron format (default is daily at midnight)  | `0 0 * * *`  |
| `image.repository`         | Repository of MapServer Docker image            | `camptocamp\mapserver`                                     | 
| `image.tag`                | Version/Tag of MapServer image                  | `7.6-20-04`                                                |
| `image.mapFilesPath`       | Path to serve map files, should be escaped with backslashes. Do not change if using the default MapServer image.    | `\\etc\\mapserver` |
| `initImage.repository`     | Repository with Docker image of the initContainer used for syncing mapfiles | `paultur\mapserver-init`  |
| `initImage.tag`            | Tag of the initContainer image                  | `0.1.0`
| `service.type`             | Kubernetes service type exposing port           | `LoadBalancer`                                             |
| `service.port`             | TCP Port for this service                       | 80                                                         |
| `resources.limits.memory`  | Pod memory resource limits in MiB (1Mi = 1 MiB)       | `1024Mi`                                |
| `resources.limits.cpu`     | Pod CPU resource limits (1000m = 1 (v)CPU core)       | `1000m`                                 |
| `autoscaling.enabled`      | Whether to apply Horizontal Pod Autoscaling (HPA) | false |
| `replicas`                 | How many instances of MapServer to deploy (if autoscaling is disabled) | 1  |
| `autoscaling.minReplicas`  | Min # of MapServer instances (if autoscaling is enabled)                                             | 1 |
| `autoscaling.maxReplicas`  | Max # of MapServer instances (if autoscaling is enabled)                                              | 10 |


## Accessing data in S3 buckets

Mapfiles could point to protected geospatial data in S3 buckets, where authentication using EC2 keypair is required (access key, secret key). Similarly, mapfiles themselves, or other artifacts (eg. .vrt files) may require protection.

CFMapserver operates with 2 sets of S3 credentials to satisfy popular default use cases:
1. S3 credentials to the location where mapfiles are stored (s3Maps section in values.yaml)
2. Another set of S3 credentials to be used by [VSIS3](https://gdal.org/user/virtual_file_systems.html#vsis3-aws-s3-files) handler used in the mapfiles (s3Geo section in values.yaml)

Providing the EC2 credentials is optional both s3Maps and S3Geo sections. If no S3 credentials are required for accessing resources in the section, use empty strings instead. The provided credentials get populated as environment variables in containers. Note that for the s3Geo section, the values provided in values.yaml will get overridden if the the individual mapfiles provide other S3 credentials in the config section.

Below, possible options for most common scenarios are listed.


| Raster images          | .vrt files (optional)                           | Mapfiles                                                   |
| -----------------------| ---------------------------------------------   | ---------------------------------------------------------- |
| public bucket          | public or private bucket                        | public or private S3 bucket                                          |
| private bucket         | public bucket or private bucket accessible with same credentials as the raster images bucket | public or private S3 bucket |
| EO data 'DIAS' bucket (CloudFerro)| public bucket                        | public or private S3 bucket |

The S3 coordinatesd (bucket, endpoint, access/secret key) could also be the same for map files and other data. In such case, the same values should be populated in s3Maps and s3Geo sections in values.yaml.

## Customizing the MapServer initialization script

Prior to deploying each MapServer container, an initialization script runs in a separate [Kubernetes initContainer](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/). The default script checks for the contents of the S3 bucket (defined in values.yaml), pulls the files with .map extension and loads them to the mounted /etc/mapserver folder. This folder gets mounted to the MapServer container as well, thus the mapfiles get synced to MapServer.

The sequence described above takes place the first time when CFMapserver is deployed, and then, with every redeployment initiated by a cronjob running on the cluster. 

The init container script can be substituted by any other script, performing custom logic e.g. applying custom changes to mapfiles prior to loading them to MapServer, pulling from different source etc. To apply such customization, you can create a custom Docker image containing a modified script and place it in a Docker repository. Then point to this image in the values.yaml (initImage.repository and initImage.tag values).

The important caveats about the custom init script:
* The script will have access to the environment variables defined in values.yaml (AWS_ACCESS_KEY_ID, AWS_SECRET_KEY, CF_S3_HOST, CF_S3_BUCKET)
* The script will have access to the /etc/mapserver folder and as a last step it should upload mapfiles to this location