"""
This function does the following:
    - Creation of a k8s configmap using dynamic-client
    - List, patch(update), delete the configmap
"""

from kubernetes import config, dynamic
from kubernetes.client import api_client
import logging as logger
import json
from jsonpatch import make_patch, apply_patch

logger.basicConfig(level=logger.INFO)
logger.getLogger("urllib3").setLevel(logger.INFO)



class ConfigMapOps:
    def __init__(self, ops):
        #Initialise the necessary parameters
        self.name = input("Enter the name of configmap or leave blank to list all configmaps: ")
        self.namespace = input("Enter the Namespace or leave blank: ")
        if not self.namespace:
            self.namespace = "default"
        # self.subscriptionid = input("Enter the SubscriptionId or leave blank")
        # self.jobid = input("Enter the JobId or leave blank")
        # self.resource = input("Enter the Resource or leave blank")
        # self.fieldselector = input("Enter the FieldSelector or leave blank")
        # self.resourcegroupname = input("Enter the ResourceGroupName or leave blank")
        # self.aksclustername = input("Enter the AksClusterName or leave blank")
        self.ops = ops

    def list_configmaps(self, client):
        logger.info("[LIST ALL CONFIGMAPS]")
        configmap_list = client.get(namespace= self.namespace)
        logger.info("The configmaps in %s namespace are:\n", self.namespace)
        for cm in configmap_list.items:
            logger.info("%s", cm["metadata"]["name"])

        return

    def get_configmap(self, client):
        logger.info("[READ CONFIGMAP]")
        configmap_get = client.get(name=self.name, namespace=self.namespace)
        for k,v in configmap_get["data"]:
            print(k,":",v)

        return configmap_get

    def create_configmap(self, client):
        logger.info("[CREATE CONFIGMAP]")
        logger.info("[NOTE]: To create a configmap, add the kv pairs in data.json file. Example: {'key1':'value1','key2':'value2'}")
        f = open("data.json")
        configmap_manifest = {
            "kind": "ConfigMap",
            "apiVersion": "v1",
            "metadata": {
                "name": self.name,
                "labels": {
                    "foo": "bar",
                },
            },
            "data": json.loads(f.read())
        }

        configmap_create = client.create(body=configmap_manifest, namespace=self.namespace)
        logger.info(configmap_create)

        return
    
    def type_cast(self, manifest):
        manifest = str(manifest.__dict__["attributes"])
        manifest =  manifest.replace("'", "\"")
        manifest = json.loads(manifest)
        return manifest        
        
    def patch_configmap(self, client):
        logger.info("[PATCH CONFIGMAP]")
        logger.info("[NOTE]: To patch a configmap, add the kv pairs in data.json file. Example: {'key1':'value1','key2':'value2'}")
        f2 = open("data.json")

        configmap_manifest = self.get_configmap(client)
        configmap_manifest = self.type_cast(configmap_manifest)

        patched_manifest = json.loads(f2.read())
        patch = make_patch(configmap_manifest["data"], patched_manifest)
        logger.info(patch)

        if int(input("Press 1 to apply patch. Press 0 to abort")) == 1:
            data = apply_patch(configmap_manifest["data"], patch)
            configmap_manifest["data"] = data
            
            print(configmap_manifest)
            
            configmap_patched = client.patch(name=self.name, namespace=self.namespace, body=configmap_manifest)
            logger.info(configmap_patched)
            
            return
        else:
            return



    def delete_configmap(self, client):
        logger.info("[DELETE CONFIGMAP]")
        configmap_manifest = self.get_configmap(client)
        configmap_manifest = self.type_cast(configmap_manifest)
        logger.info("[KVs]:", configmap_manifest["data"])
        delete = int(input("Are you sure you want to delete the resource? Press 1 to continue: "))
        if delete == 1:
            with open("{name}.json".format(name = self.name), 'w') as f:
                json.dump(configmap_manifest, f)
            configmap_deleted = client.delete(name=self.name, body={}, namespace=self.namespace)
        logger.info("Configmap is deleted.")

        return

#Take input from user for all parameters
ops = int(input("Enter 0 to list configmaps.\n Enter 1 to read a configmap kv.\n Enter 2 to create a configmap.\n Enter 3 to patch a configmap.\n Enter 4 to delete a configmap.\n"))
cm_object = ConfigMapOps(ops)

client = dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config())
    )

cm_client = client.resources.get(api_version="v1", kind="ConfigMap")

match ops:
    case 0:
        cm_object.list_configmaps(cm_client)
    case 1:
        cm_object.get_configmap(cm_client)
    case 2:
        cm_object.create_configmap(cm_client)
    case 3:
        cm_object.patch_configmap(cm_client)
    case 4:
        cm_object.delete_configmap(cm_client)
    
    