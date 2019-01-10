Clone repositories hosted on GitHub to buckets in Oracle Cloud Infrastructure Object Storage

#Required packages:
Python 3
Pipenv

#Recommended packages:
OCI CLI

#Install steps:

Run `git clone https://github.com/rosalexander/oci-git.git`

Run `cd oci-git`

Run `pipenv install`

Run `pipenv shell`

#Commands:
```
python3 oci-git.py git clone <username> <repo_name>
     Clones the GitHub repository under the username and creates a bucket in the compartment OCID on file
python3 oci-git.py delete bucket <bucket_name>
     Deletes the bucket and all associated objects in the compartment OCID on file
python3 oci-git.py modify <variable name> <variable value>
     Modifies the variables in config.json
python3 oci-git.py list (optional) <variable name>
     Prints out the variables in config.json
```
