# Sample GUID client

## Installation instructions

Create virtualenv:

````
virtualenv -p /usr/bin/python3.5 .venv

. .venv/bin/activate

pip install -r pip.requirements
````

## Testing instructions

Specify a --url of mock://test.net to simulate a server and display responses.
Using the mock:// url with a guid that starts with '8' will generate a HTTP Client error and a guid that starts with '9' will generate a HTTP Server Error.

## CLI usages

````
usage: client.py [-h] [--version] {create,read,update,delete} ...

GUID client

positional arguments:
  {create,read,update,delete}
                        '[sub-command] -h' for further help on listed sub-
                        commands
    create              create a GUID
    read                read a GUID
    update              update a GUID
    delete              delete a GUID

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
````


## create GUID

````
usage: client.py create [-h] [-e EXPIRE] -u USER [-g GUID] --url URL

optional arguments:
  -h, --help            show this help message and exit
  -e EXPIRE, --expire EXPIRE
                        expiration time for guid specified in seconds in epoch
  -u USER, --user USER  user
  -g GUID, --guid GUID  guid
  --url URL             endpoint URL
````

## update GUID

````
usage: client.py update [-h] -g GUID -e EXPIRE --url URL

optional arguments:
  -h, --help            show this help message and exit
  -g GUID, --guid GUID  guid
  -e EXPIRE, --expire EXPIRE
                        expiration time for guid specified in seconds in epoch
  --url URL             endpoint URL

````

## read GUID 

````
usage: client.py read [-h] -g GUID --url URL

optional arguments:
  -h, --help            show this help message and exit
  -g GUID, --guid GUID  guid
  --url URL             endpoint URL
````

## delete GUID

````
usage: client.py delete [-h] -g GUID --url URL

optional arguments:
  -h, --help            show this help message and exit
  -g GUID, --guid GUID  guid
  --url URL             endpoint URL

````
