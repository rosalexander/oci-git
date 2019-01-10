import sys
import oci
import os
import requests
from urllib.request import urlopen
from mimetypes import guess_type
import json

# config = {}
# identity = None
variables = ["access_token", "compartment_id,", "tenancy", "user", "key_file", "fingerprint", "region", "pass_phrase"]

def validate():
    try:
        config = oci.config.from_file()
    except:
        print("Default OCI config file at '~/.oci/config' either missing or invalid. Switching to './config.json'")
        with open("config.json", "r+") as jsonFile:
            data = json.load(jsonFile)
            config = {
                "user": data["user"],
                "key_file": data["key_file"],
                "fingerprint": data["fingerprint"],
                "tenancy": data["tenancy"],
                "region": data["region"],
                "pass_phrase": data["pass_phrase"]
            }

            jsonFile.seek(0)
            json.dump(data, jsonFile)
            jsonFile.truncate()
    try:
        oci.config.validate_config(config)
    except:
        print("OCI config variables either missing or invalid. Please input them.")
        with open("config.json", "r+") as jsonFile:
            data = json.load(jsonFile)

            config["user"] = input("User OCID: ")
            config["tenancy"] = input("Tenancy OCID: ")
            config["region"] = input("Region: ")
            config["key_file"] = input("PEM key file path: ")
            config["fingerprint"] = input("PEM key fingerprint: ")
            config["pass_phrase"] = input("PEM key passphrase: ")

            data["user"] = config["user"]
            data["key_file"] = config["key_file"]
            data["fingerprint"] = config["fingerprint"]
            data["tenancy"] = config["tenancy"]
            data["region"] = config["region"]
            data["pass_phrase"] = config["pass_phrase"]
            
            jsonFile.seek(0)
            json.dump(data, jsonFile)
            jsonFile.truncate()
        
    with open("config.json", "r+") as jsonFile:
        data = json.load(jsonFile)
        config["access_token"] = data["access_token"]
        config["compartment_id"] = data["compartment_id"]
        modified = False
        if not config["access_token"]:
            config["access_token"] = input("GitHub access token: ")
            data["access_token"] = config["access_token"]
            modified = True
        if not config["compartment_id"]:
            config["compartment_id"] = input("Compartment OCID: ")
            data["compartment_id"] = config["compartment_id"]
            modified = True
        if modified:
            jsonFile.seek(0)
            json.dump(data, jsonFile)
            jsonFile.truncate()
    
    return config


def get_config_value(key):
    return config[key]

def change_config_value(key, value):
    with open("config.json", "r+") as jsonFile:
        data = json.load(jsonFile)
        data[key] = value
        jsonFile.seek(0)
        json.dump(data, jsonFile)
        jsonFile.truncate()

def clone_github_repo(username, repo, created):

    if not created:
        object_storage = oci.object_storage.ObjectStorageClient(config)
        namespace = object_storage.get_namespace().data
        request = oci.object_storage.models.CreateBucketDetails()
        request.compartment_id = config["compartment_id"]
        request.name = repo
        bucket = object_storage.create_bucket(namespace, request)

    path = ''
    queue = [path]
    discovered = [path]

    while queue:
        search = queue.pop()
        response = requests.get('https://api.github.com/repos/' + username + '/' + repo + '/contents/' + search + "?access_token=" + config["access_token"])
        for f in response.json():
            if (f['type'] == 'dir'):
                if f['path'] not in discovered:
                    queue.append(f['path'])
                    discovered.append(f['path'])
            else:
                content_type = guess_type(f['download_url'])
                if content_type[0] == None:
                    content_type = 'application/octet-stream'
                data = urlopen(f['download_url']) # it's a file like object and works just like a file
                obj = object_storage.put_object(namespace, bucket.data.name, f['path'], data.read(), content_type=content_type[0])
                print("Creating " + f['path'])

    
def delete_bucket(namespace_name, bucket_name):
    object_storage = oci.object_storage.ObjectStorageClient(config)
    response = object_storage.list_objects(namespace_name, bucket_name)
    if response.data:
        for object_summary in response.data.objects:
            print("Deleting " + object_summary.name)
            object_storage.delete_object(namespace_name, bucket_name, object_summary.name)

    print("Deleting bucket " + bucket_name)
    object_storage.delete_bucket(namespace_name, bucket_name)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'git':
            if len(sys.argv) > 4:
                if sys.argv[2] == 'clone':
                    config = validate()
                    clone_github_repo(sys.argv[3], sys.argv[4], False)
            else:
                print("Error: Arguments must be formatted 'python3 oci-git.py git clone <username> <repo_name>'")
        if sys.argv[1] == 'delete':
            config = validate()
            if len(sys.argv) > 3:
                if sys.argv[2] == 'bucket':
                    identity = oci.identity.IdentityClient(config)
                    response = identity.get_tenancy(config['tenancy'])
                    delete_bucket(response.data.name, sys.argv[3])
            else:
                print("Error: Arguments must be formatted 'python3 oci-git.py delete bucket <bucket_name>'")
        if sys.argv[1] == 'modify':
            if len(sys.argv) > 3:
                if sys.argv[2] in variables:
                    change_config_value(sys.argv[2], sys.argv[3])
                else:
                    print("Variable must be in list " + str(variables))
            else:
                print("Error: Arguments must be formatted 'python3 oci-git.py modify compartment_id/access_token/tenancy_name/etc <compartment_id>/<access_token>/<tenancy>/etc'")
        if sys.argv[1] == 'list':
            config = validate()
            if len(sys.argv) > 2:
                if sys.argv[2] in variables:
                    print(sys.argv[2] + ": " + config[sys.argv[2]])
                else:
                    print("Variable must be in list " + str(variables))

            else:
                print("compartment_id: " + config["compartment_id"])
                print("access_token: " + config["access_token"])
                print("tenancy: " + config['tenancy'])
                print("user: " + config['user'])
                print("key_file: " + config['key_file'])
                print("fingerprint: " + config['fingerprint'])
                print("region: " + config['region'])

        if sys.argv[1] == 'help':
            print("python3 oci-git.py git clone <username> <repo_name>")
            print("     Clones the GitHub repository under the username and creates a bucket in the compartment OCID on file")
            print("python3 oci-git.py delete bucket <bucket_name>")
            print("     Deletes the bucket and all associated objects in the compartment OCID on file")
            print("python3 oci-git.py modify <variable name> <variable value>")
            print("     Modifies the variables in config.json")
            print("python3 oci-git.py list (optional) <variable name>")
            print("     Prints out the variables in config.json")
    else:
        print("No arguments given. Enter 'python3 oci-git.py help' to see usage.")