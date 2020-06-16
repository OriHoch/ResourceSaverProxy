# Resource Saver Proxy

Provides a REST API / web page which is shown before access to a resource.

This page allows to request access to the resource for a given amount of time.

It ensures the resource is available.

After the requested amount of time is passed, the resource is turned off.

## Quickstart

Install from source

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Create a configuration file

```
resources:
  my-resource:
    resource:
      type: google-cloud-instance
      googleProjectId: my-google-project
      instanceId: my-instance-id
      zone: europe-west2-a
    access:
      type: web
      url: http://access.my-instance.com/
    auth:
      type: password
      userPassword: "123456"
      adminPassword: "654321"
    userLimits:
      maxHours: 2
    adminLimits:
      maxHours: 10
```

Set the location of the env file in env var:

```
export RSP_CONFIG=/path/to/config/file
```

Set path to store run-time data:

```
export RSP_RUNTIME_DATA=/var/run/resourcesaverproxy
```

Make sure you installed and are logged-in to google cloud CLI

## API reference

Examples use the CLI for easy testing / development but you can also use the REST api, see below

All commands have a first `<AUTH>` parameter which contains auth details depending on the resource auth config

For password type auth the value should be `user:PASSWORD` or `admin:PASSWORD`

### Activate resource

Activate a resource for given amount of time (doesn't wait for resource to be active)

```
rsp activate <AUTH> <RESOURCE_ID> <NUM_HOURS> 
```

### Get resource status

Returns true when resource is activated and ready for access

```
rsp get-status <AUTH> <RESOURCE_ID>
```

### Get access details to a resource

This should run after resource status is true to see how to access it

```
rsp get-access <AUTH> <RESOURCE_ID>
```

### Get resource deactivation time

Returns a date/time format `%Y-%m-%d %H:%M` for the deactivation time of the resource.

Returns an empty string if resource was never requested for activation.

AUTH must correspond to an admin user.

```
rsp get-deactivation-time <AUTH> <RESOURCE_ID>
```

### Force deactivate resource

Force deactivation of a resource, regardless of activation requests

AUTH must correspond to an admin user.

```
rsp force-deactivate <AUTH> <RESOURCE_ID>
```

## REST/WEB API

Start the REST/WEB API for development

```
env FLASK_APP=resourcesaverproxy.web flask run
```

Start for production

```
gunicorn -b 0.0.0.0:5000 -w 2 resourcesaverproxy.web:app
```

### REST API

* `/activate?auth=&resource_id=&num_hours=`
* `/get_status?auth=&resource_id=`
* `/get_access?auth=&resource_id=`

Response status_code indicates success or failure

Response body is a json object with the following keys:

* `ok` - boolean indicating success or failure
* `error` - only returned in case of error, contains string with the error message
* additional method specific keys might also be returned

### WEB Interface

* `/web?resource_id=`

Show a form to request access, after it's submitted, user is redirected according to access config.

## Deactivation daemon

The daemon checks the requested times and deactivates resources when needed

Starts the daemon

```
rsp start-deactivation-daemon
```
