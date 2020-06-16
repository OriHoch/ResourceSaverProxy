import click
import ruamel.yaml
import sys
from ruamel.yaml.representer import RoundTripRepresenter


class MyRepresenter(RoundTripRepresenter):
    pass


def _yaml_dump_object(obj):
    yaml = ruamel.yaml.YAML()
    yaml.Representer = MyRepresenter
    yaml.dump(obj, sys.stdout)
    sys.stdout.flush()


@click.group()
def main():
    pass


from . import api


@main.command()
@click.argument('AUTH')
@click.argument('RESOURCE_ID')
@click.argument('NUM_HOURS')
def activate(auth, resource_id, num_hours):
    api.activate(auth, resource_id, num_hours)
    print("OK")


@main.command()
@click.argument('AUTH')
@click.argument('RESOURCE_ID')
def get_status(auth, resource_id):
    print("Ready" if api.get_status(auth, resource_id) else "Not Ready")


@main.command()
@click.argument('AUTH')
@click.argument('RESOURCE_ID')
def get_access(auth, resource_id):
    _yaml_dump_object(api.get_access(auth, resource_id))


@main.command()
@click.argument('AUTH')
@click.argument('RESOURCE_ID')
def get_deactivation_time(auth, resource_id):
    print(api.get_deactivation_time(auth, resource_id))


@main.command()
@click.argument('AUTH')
@click.argument('RESOURCE_ID')
def force_deactivate(auth, resource_id):
    api.force_deactivate(auth, resource_id)
    print("OK")


@main.command()
def start_deactivation_daemon():
    api.start_deactivation_daemon()
