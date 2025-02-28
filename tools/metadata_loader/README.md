# Metadata loader tool

This python script reads sigMF metadata files from the given container in an Azure storage blob account or an Azure ADLS gen2 account and inserts them into the RFDX database. It does this by calling RFDX api methods. It is a command line interface program.

The commands can be found by the "-h" argument as such:

usage: main.py [-h] {datasource,metadata} ...

Tools for working with a metadata database.

positional arguments:
  {datasource,metadata}

options:
  -h, --help            show this help message and exit

To add metadata, there must be a datasource. Hence, the cli provides a way to add a datasource, list existing datasources, add a container full of metadata, and list metadata currently in the database for the designated datasource.

The tool looks for all files with the '.sigmf-meta' file extension in the given account/container. It looks through all folders in the container. It assumes that the files contain valid sigMF metadata json.

The tool connects to Azure storage using credentials in the .env file. sample.env is provided.
