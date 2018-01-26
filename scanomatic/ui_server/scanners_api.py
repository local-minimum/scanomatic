from __future__ import absolute_import
from datetime import datetime
from httplib import NOT_FOUND, OK, BAD_REQUEST

from flask import request, jsonify, Blueprint, current_app
from flask_restful import Api, Resource
import pytz
from werkzeug.exceptions import NotFound

from .general import json_abort
from .serialization import job2json
from scanomatic.io.scanning_store import ScannerStatus

blueprint = Blueprint("scanners_api", __name__)


@blueprint.route("", methods=['GET'])
def scanners_get():
    get_free = request.args.get('free', False)
    scanning_store = current_app.config['scanning_store']
    scanners = (
        scanning_store.get_free_scanners() if get_free else
        scanning_store.get_all_scanners()
    )
    return jsonify([scanner._asdict() for scanner in scanners])


@blueprint.route("/<scanner>", methods=['GET'])
def scanner_get(scanner):
    scanning_store = current_app.config['scanning_store']
    if scanning_store.has_scanner(scanner):
        return jsonify(**scanning_store.get_scanner(scanner)._asdict())
    return json_abort(
        NOT_FOUND, reason="Scanner '{}' unknown".format(scanner)
    )


@blueprint.route("/<scanner>/status", methods=['POST'])
def scanner_status_update(scanner):
    scanning_store = current_app.config['scanning_store']
    if not scanning_store.has_scanner(scanner):
        # TODO: should create non-existent
        return json_abort(
            NOT_FOUND,
            reason="Scanner '{}' unknown".format(scanner)
        )

    status = request.get_json(silent=True, force=True)
    try:
        scanning_store.add_scanner_status(
            scanner, ScannerStatus(
                status["job"], datetime.utcnow(), status["message"]))
    except KeyError:
        return json_abort(
            BAD_REQUEST,
            reason="Got malformed status '{}'".format(status)
        )

    return "", OK


@blueprint.route("/<scanner>/status", methods=['GET'])
def scanner_status_get(scanner):
    scanning_store = current_app.config['scanning_store']
    if scanning_store.has_scanner(scanner):
        status = scanning_store.get_latest_scanner_status(scanner)
        if status is None:
            status = ScannerStatus(None, None, None)
        return jsonify(**status._asdict())
    return json_abort(
        NOT_FOUND, reason="Scanner '{}' unknown".format(scanner)
    )


class ScannerJob(Resource):
    def get(self, scannerid):
        db = current_app.config['scanning_store']
        if not db.has_scanner(scannerid):
            raise NotFound
        job = db.get_current_scanjob(scannerid, datetime.now(pytz.utc))
        if job:
            return job2json(job)


api = Api(blueprint)
api.add_resource(ScannerJob, '/<scannerid>/job', endpoint='scanner-job')
