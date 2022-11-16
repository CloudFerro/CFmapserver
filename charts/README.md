# How to use this chart?

Add repository locally:

```
helm repo add cfmapserver https://PoulTur.github.io/cfmapserver/charts
```


Verify the repo was added:

```
helm search repo
```

Create a customization file my-values.yaml by pulling the default file, then edit this file. At minimum, fill in the S3 coordinates (name of your bucket and S3 credentials). You can also override other default values, in line with the configuration guidelines.

```
wget https://raw.githubusercontent.com/PoulTur/cfmapserver/main/charts/values.yaml -O my-values.yaml
```


Install the chart. We are adding here the custom flags --namespace and --create-namespace in order to have all artifacts contained in a dedicated namespace. You could skip these flags to upload to the default namespace instead, then you will not need to apply the -n flag when browsing for resources.

```
helm install cfmapserver cfmapserver/CFmapserver -f custom-values.yaml --namespace cfmapserver --create-namespace
```

Check that the service is running:
```
kubectl get services
```

After a couple minutes you should see a public IP running.