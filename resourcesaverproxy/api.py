import os
import ruamel.yaml
import subprocess
import json
import requests
import datetime
import time
import traceback


with open(os.environ["RSP_CONFIG"]) as f:
    CONFIG = ruamel.yaml.safe_load(f)


def _get_resource_config(resource_id):
    return CONFIG["resources"][resource_id]


def _get_resource_auth(resource_config, auth):
    if resource_config["auth"]["type"] == "password":
        tmp = auth.split(":")
        username, password = tmp[0], ":".join(tmp[1:])
        if username in ["user", "admin"]:
            if resource_config["auth"]["%sPassword" % username] == password:
                limits = resource_config.get("%sLimits" % username, {})
                return {"limits": dict(limits), "is_admin": username == "admin"}
            else:
                raise Exception("invalid auth details")
        else:
            raise Exception("invalid auth details")
    else:
        raise Exception("unsupported auth type: %s" % resource_config["auth"]["type"])


def _check_resource_access_status(acc):
    if acc["type"] == "web":
        try:
            res = requests.get(acc["url"], timeout=15)
        except Exception:
            traceback.print_exc()
            return False
        status_code = res.status_code
        res.close()
        return status_code == 200
    else:
        raise Exception("unsupported access type %s" % acc["type"])


def _get_resource_access(acc):
    if acc["type"] == "web":
        return {"url": acc["url"]}
    else:
        raise Exception("unsupported access type %s" % acc["type"])


def _get_resource_status(resource_config):
    res = resource_config["resource"]
    if res["type"] == "google-cloud-instance":
        status = json.loads(subprocess.check_output(["gcloud", "--project", res["googleProjectId"], "compute", "instances", "describe", res["instanceId"], "--format", "json", "--zone", res["zone"]]))
        if status["status"] == "RUNNING":
            return _check_resource_access_status(resource_config["access"])
        else:
            return False
    else:
        raise Exception("unsupported resource type: %s" % res["type"])


def _get_droptime(resource_id):
    filename = os.path.join(os.environ["RSP_RUNTIME_DATA"], resource_id)
    if os.path.exists(filename):
        with open(filename) as f:
            return datetime.datetime.strptime(f.read(), "%Y%m%d%H%M")
    else:
        return None


def _set_droptime(resource_id, droptime):
    filename = os.path.join(os.environ["RSP_RUNTIME_DATA"], resource_id)
    if droptime:
        with open(filename, "w") as f:
            f.write(droptime.strftime("%Y%m%d%H%M"))
    elif os.path.exists(filename):
        os.unlink(filename)


def _runPostActivateResourceScripts(res, ip):
    for script in res.get("postActivateScripts"):
        subprocess.check_call(script, shell=True, env={**os.environ, "IP": ip})


def _activate_resource(res):
    if res["type"] == "google-cloud-instance":
        status = json.loads(subprocess.check_output(["gcloud", "--project", res["googleProjectId"], "compute", "instances", "describe", res["instanceId"],"--format", "json", "--zone", res["zone"]]))
        if status["status"] != "RUNNING":
            subprocess.check_call(["gcloud", "--project", res["googleProjectId"], "compute", "instances", "start", res["instanceId"], "--zone", res["zone"]])
            time.sleep(10)
            status = json.loads(subprocess.check_output(["gcloud", "--project", res["googleProjectId"], "compute", "instances", "describe", res["instanceId"], "--format", "json", "--zone", res["zone"]]))
        ip = ""
        for networkInterface in status["networkInterfaces"]:
            for accessConfig in networkInterface["accessConfigs"]:
                if accessConfig["name"] == "External NAT":
                    ip = accessConfig["natIP"]
                    break
            if ip: break
        _runPostActivateResourceScripts(res, ip)
    else:
        raise Exception("invalid resource type %s" % res["type"])


def _deactivate_resource(res):
    if res["type"] == "google-cloud-instance":
        status = json.loads(subprocess.check_output(["gcloud", "--project", res["googleProjectId"], "compute", "instances", "describe", res["instanceId"],"--format", "json", "--zone", res["zone"]]))
        if status["status"] == "RUNNING":
            subprocess.check_call(["gcloud", "--project", res["googleProjectId"], "compute", "instances", "stop", res["instanceId"], "--zone", res["zone"]])
    else:
        raise Exception("invalid resource type %s" % res["type"])


def activate(auth, resource_id, num_hours):
    num_hours = int(num_hours)
    resource_config = _get_resource_config(resource_id)
    user = _get_resource_auth(resource_config, auth)
    max_hours = int(user["limits"].get("maxHours", 0))
    if 0 < max_hours < num_hours:
        raise Exception("maximum number of hours is limited to %s" % max_hours)
    else:
        req_droptime = datetime.datetime.now() + datetime.timedelta(hours=num_hours)
        cur_droptime = _get_droptime(resource_id)
        if not cur_droptime or cur_droptime < req_droptime:
            _set_droptime(resource_id, req_droptime)
        _activate_resource(resource_config["resource"])


def get_status(auth, resource_id):
    resource_config = _get_resource_config(resource_id)
    _ = _get_resource_auth(resource_config, auth)
    return _get_resource_status(resource_config)


def get_access(auth, resource_id):
    resource_config = _get_resource_config(resource_id)
    _ = _get_resource_auth(resource_config, auth)
    return _get_resource_access(resource_config["access"])


def get_deactivation_time(auth, resource_id):
    resource_config = _get_resource_config(resource_id)
    user = _get_resource_auth(resource_config, auth)
    if user["is_admin"]:
        droptime = _get_droptime(resource_id)
        return droptime.strftime("%Y-%m-%d %H:%M") if droptime else ""
    else:
        raise Exception("invalid auth details")


def force_deactivate(auth, resource_id):
    resource_config = _get_resource_config(resource_id)
    user = _get_resource_auth(resource_config, auth)
    if user["is_admin"]:
        _deactivate_resource(resource_config["resource"])
    else:
        raise Exception("invalid auth details")


def start_deactivation_daemon():
    while True:
        for resource_id, resource_config in CONFIG["resources"].items():
            droptime = _get_droptime(resource_id)
            if droptime and datetime.datetime.now() >= droptime:
                print("Deactivating resource %s" % resource_id)
                _deactivate_resource(resource_config["resource"])
                _set_droptime(resource_id, None)
        time.sleep(60)
