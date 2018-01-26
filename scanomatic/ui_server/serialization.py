from __future__ import absolute_import
from scanomatic.util.datetime import is_utc


def job2json(job):
    obj = {
        'identifier': job.identifier,
        'name': job.name,
        'duration': job.duration.total_seconds(),
        'interval': job.interval.total_seconds(),
        'scannerId': job.scanner_id,
    }
    if job.start_time is not None:
        assert is_utc(job.start_time)
        obj['startTime'] = job.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    return obj


def status2json(status):
    obj = {
        'job': status.job,
        'message': status.message,
    }
    if status.server_time is None:
        obj['serverTime'] = None
    else:
        assert is_utc(status.server_time)
        obj['serverTime'] = status.server_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    return obj
