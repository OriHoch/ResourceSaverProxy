from flask import Flask, request, render_template
from . import api


app = Flask(__name__)


@app.route('/activate')
def activate():
    try:
        api.activate(**dict(request.args))
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500


@app.route('/get_status')
def get_status():
    try:
        return {'ok': True, 'status': api.get_status(**dict(request.args))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500


@app.route('/get_access')
def get_access():
    try:
        return {'ok': True, 'access': api.get_access(**dict(request.args))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500


@app.route('/get_deactivation_time')
def get_deactivation_time():
    try:
        return {'ok': True, 'deactivation_time': api.get_deactivation_time(**dict(request.args))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500


@app.route('/force_deactivate')
def force_deactivate():
    try:
        api.force_deactivate(**dict(request.args))
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}, 500


@app.route('/web')
def web():
    return render_template("web.html", resource_id=request.args["resource_id"])
