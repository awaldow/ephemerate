#!/usr/bin/env python3
"""Ephemerator - Ephemerate Kubernetes Resources"""
import datetime
import os
import time
import kopf
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import pytz

try:
    k8s_config.load_kube_config()
except k8s_config.ConfigException:
    k8s_config.load_incluster_config()

# pylint: disable=fixme
# TODO: Getting some very annoying errors related to libcrypto not being found even though it's there.
# Doesn't seem to be an OOM issue as pointed out in an SO post, as I put the request up super high
# and am still getting the same issue.
# @kopf.on.startup()
# def configure(settings: kopf.OperatorSettings, **_):
#     settings.admission.server = kopf.WebhookServer(
#         addr='0.0.0.0', port=8443)

# TODO: Would like to get self-registration and -cleanup working at some point, but for now
#   we'll let helm manage the CRD lifecycle
# try:
#     print('registering Ephemerator CRD with cluster API')
#     k8s_client.ApiextensionsV1Api().create_custom_resource_definition(ephemerator_crd)
# except k8s_client.rest.ApiException as e:
#     if e.status == 409:
#         print("CRD already exists")
#     else:
#         raise e


CURRENT_VERSION = 'v1alpha1'

# region v1alpha1


def get_until_seconds(until, logger, **_):
    """
    Converts an ephemerator "until" object into a unix timestamp.

    Parameters
    ----------
    until : obj
        Contains a date, time (in 24hr format), and timezone

    Returns
    -------
    int
        An integer representing the seconds until the given time.

    Examples
    --------
    >>> get_until_seconds({'date': '2021-12-07', 'time': '18:00:00', 'timezone': 'America/Los_Angeles'}) # from 12/7/2021 at 5pm PST
    3600
    """
    format_string = '%Y-%m-%dT%H:%M:%S'
    date_string = until["date"] + 'T' + until["time"]
    logger.info(f'dateString == {date_string}')
    provided_timezone = pytz.timezone(until["timezone"])
    logger.info(f'providedTimezone == {provided_timezone}')
    local_date_time = provided_timezone.localize(
        datetime.datetime.strptime(date_string, format_string), is_dst=None)
    logger.info(f'localDateTime == {local_date_time}')
    logger.info(f'localDateTime.timestamp() == {local_date_time.timestamp()}')
    logger.info(
        f'time now == {datetime.datetime.today().strftime("%m/%d/%Y %H:%M:%S")}')
    logger.info(f'time.time() == {str(time.time())}')
    return int(local_date_time.timestamp() - time.time())


def get_duration_seconds(duration, logger, **_):
    """
    Converts an ephemerator "duration" object into a unix timestamp.

    Parameters
    ----------
    until : obj
        Contains at least one of years, months, weeks, days, hours, minutes, and seconds

    Returns
    -------
    int
        An integer representing the total seconds for the duration provided.

    Examples
    --------
    >>> get_duration_seconds({ 'hours': 1 })
    3600
    """
    time_dict = {'weeks': ((duration.get("years", 0) * 52) +
                           (duration.get("months", 0) * 4) +
                           duration.get("weeks", 0)),
                 'days': duration.get("days", 0),
                 'hours': duration.get("hours", 0),
                 'minutes': duration.get("minutes", 0),
                 'seconds': duration.get("seconds", 0)}
    logger.info('timedict == %s' % time_dict)
    return datetime.timedelta(**time_dict).total_seconds()

# We are handling most of this using OpenAPIv3 Schema validation stuff, but would still
# like to get this working at some point
# to maybe just reject ephemerators defined against ignored namespaces/namespaces
# that don't exist/etc without the CRD being created in the first place

# @kopf.on.validate('tessellate.io', 'v1alpha1', 'ephemerators')
# def validate(spec, warnings, logger, **_):
#     logger.info('validating ephemerator spec')
#     if 'until' in spec["lifetime"] and 'duration' in spec["lifetime"]:
#         warnings.append(
#             "Only one of spec.lifetime.duration and spec.lifetime.until will be honored, 'until' takes precedence.")
#     if 'until' not in spec["lifetime"] and 'duration' not in spec["lifetime"]:
#         raise kopf.AdmissionError(
#             "Either spec.liftime.until or spec.lifetime.duration must be defined", code=400)
#     if 'duration' in spec["lifetime"]:
#         if not spec["lifetime"]["duration"]:
#             raise kopf.AdmissionError(
#                 "spec.lifetime.duration must have some units defined, from minutes to years", code=400)
#     if 'until' in spec["lifetime"]:
#         if not spec["lifetime"]["until"]:
#             raise kopf.AdmissionError(
#                 "spec.lifetime.until must have 'date', 'time' and 'timezone' defined", code=400)


@kopf.on.create('tessellate.io', 'v1alpha1', 'ephemerators')
def on_create(spec, logger, meta, **_):
    """
    CREATE handler for ephmerators.

    Parameters
    ----------
    spec:
        The spec for the ephemerator to create
    logger:
        The logger
    meta:
        The metadata for the ephemerator to create
    **_:
        Unused

    Returns
    -------
    obj
        object that will be added to the ephemerator's status under on_create:
    """
    logger.info('new Ephemerator created')
    seconds_until_expiration = 0
    if 'until' in spec["lifetime"]:
        seconds_until_expiration = get_until_seconds(
            spec['lifetime']['until'], logger)
    elif 'duration' in spec["lifetime"]:
        seconds_until_expiration = get_duration_seconds(
            spec['lifetime']['duration'], logger)
    creation_timestamp = meta['creationTimestamp']
    created_date_time = datetime.datetime.strptime(
        creation_timestamp, '%Y-%m-%dT%H:%M:%SZ')
    created_seconds = (created_date_time -
                       datetime.datetime(1970, 1, 1)).total_seconds()
    logger.info(f'lifetime equates to {str(seconds_until_expiration)} seconds')
    expires_at = created_seconds + \
        datetime.timedelta(seconds=seconds_until_expiration).total_seconds()
    return {
        'expiresAtSeconds': expires_at,
        'expiresAt': datetime.datetime.fromtimestamp(expires_at).strftime("%m/%d/%Y, %H:%M:%S")
    }


@kopf.on.update('tessellate.io', 'v1alpha1', 'ephemerators')
def on_update(name, spec, meta, logger, **_):
    """
    Update handler for ephmerators.

    Unlike on_create, this method will not explicitly return anything, but will patch the ephemerator's status instead.

    Parameters
    ----------
    name:
        The name of the ephemerator to update
    spec:
        The spec for the ephemerator to update
    meta:
        The metadata for the ephemerator to update
    logger:
        The logger
    **_:
        Unused
    """
    logger.info('Ephemerator updated, recalculating status')
    creation_timestamp = meta['creationTimestamp']
    created_date_time = datetime.datetime.strptime(
        creation_timestamp, '%Y-%m-%dT%H:%M:%SZ')
    created_seconds = (created_date_time -
                       datetime.datetime(1970, 1, 1)).total_seconds()
    seconds_until_expiration = 0
    if 'until' in spec["lifetime"]:
        seconds_until_expiration = get_until_seconds(
            spec['lifetime']['until'], logger)
    elif 'duration' in spec["lifetime"]:
        seconds_until_expiration = get_duration_seconds(
            spec['lifetime']['duration'], logger)
    logger.info(
        f'new lifetime equates to {str(seconds_until_expiration)} seconds')
    expires_at = created_seconds + \
        datetime.timedelta(seconds=seconds_until_expiration).total_seconds()
    k8s_client.CustomObjectsApi().patch_cluster_custom_object('tessellate.io', 'v1alpha1', 'ephemerators', name, {
        'status':
        {
            'on_update': {
                'expiresAtSeconds': expires_at,
                'expiresAt': datetime.datetime.fromtimestamp(expires_at).strftime("%m/%d/%Y, %H:%M:%S")
            }
        }
    })


def namespace_expired(status, logger, **_):
    """
    Check if the ephemerator has expired.

    Checks the status for expiresAtSeconds, and if it is defined, checks if time.time() >= expiresAtSeconds. Because of the way kopf works,
    we have to check if on_update exists and use that instead of the on_create status.

    Parameters
    ----------
    status:
        The status of the ephemerator to check
    logger:
        The logger
    **_:
        Unused
    """
    logger.info('checking that namespace has not expired')
    logger.info(f'time.time() == {str(time.time())}')
    expired = False
    if 'on_update' in status:
        expired = time.time() >= status["on_update"]["expiresAtSeconds"]
        logger.info(
            f'ephemerator.status.on_update.expiresAtSeconds == {str(status["on_update"]["expiresAtSeconds"])}')
    elif 'on_create' in status:
        expired = time.time() >= status["on_create"]["expiresAtSeconds"]
        logger.info(
            f'ephemerator.status.on_create.expiresAtSeconds == {str(status["on_create"]["expiresAtSeconds"])}')
    logger.info(
        f'time.time() >= ephemerator.status.expiresAtSeconds == {expired}')
    return expired


def not_ignored_namespace(spec, logger, **_):
    """
    Check if the ephemerator is configured to delete a default or ignored resource.

    By default, the 'default' and any 'kube-*' namespaces are ignored. If you want to explicitly ignore more, add them in
    a comma delimited list to EPHEMERATOR_IGNORED_NAMESPACES in the ephemerator config.

    Parameters
    ----------
    spec:
        The spec of the ephemerator to check
    logger:
        The logger
    **_:
        Unused
    """
    logger.info(
        'checking that we are only ephemerating non-required/non-ignored namespaces. Timer will not start when ignoredNamespace == True')
    ignore_namespaces = os.environ.get(
        'EPHEMERATOR_IGNORE_NAMESPACES', '').split(',')
    logger.info(
        f'ignoring namespaces: default, kube-* (, {",".join(ignore_namespaces)})')
    ignored_namespace = spec["resourceToWatch"]["namespace"] == 'default' or spec["resourceToWatch"]["namespace"].startswith(
        'kube-')
    for ignore_namespace in ignore_namespaces:
        ignored_namespace = ignored_namespace or spec["resourceToWatch"]["namespace"] == ignore_namespace
    logger.info(f'ignoredNamespace == {ignored_namespace}')
    return not ignored_namespace


@kopf.timer('tessellate.io', 'v1alpha1', 'ephemerators',
            interval=int(os.environ.get('EPHEMERATE_INTERVAL')),
            annotations={'ephemerators.tessellate.io/enabled': 'true'},
            when=not_ignored_namespace)
def ephemerate(spec, status, meta, logger, **_):
    """
    Timer to delete the ephemerated resource.

    Runs every EPHEMERATE_INTERVAL seconds, and checks if the ephemerator has expired. If it has, it will delete the resource
    and, after that, the ephemerator itself. Timers will only be registered for ephemerators that have the
    'ephemerators.tessellate.io/enabled' annotation set to 'true' and are not pointing to an ignored or default resource.

    Parameters
    ----------
    spec:
        The spec of the ephemerator to check
    status:
        The status of the ephemerator to check
    meta:
        The metadata of the ephemerator to check
    logger:
        The logger
    **_:
        Unused
    """
    logger.info('ephemerate called, evaluating ephemerator')
    # TODO: Would be nice to have some kind of approval workflow as a final check before deleting, and an annotation to disable that functionality
    # TODO: Would be nice to have an email/event/notification sent when namespace is going to be deleted to let people know what's going on
    # if notIgnoredNamespace(spec, logger) and namespaceExpired(status, logger):
    if namespace_expired(status, logger):
        # TODO: Should wait here and make 100% sure that the namespace (and all its children) is deleted
        logger.info(
            f'deleting namespace {spec["resourceToWatch"]["namespace"]}')
        k8s_client.CoreV1Api().delete_namespace(
            spec["resourceToWatch"]["namespace"])
        logger.info(f'deleting ephemerator {meta["name"]}')
        k8s_client.CustomObjectsApi().delete_cluster_custom_object(
            'tessellate.io', 'v1alpha1', 'ephemerators', meta["name"])
# endregion
