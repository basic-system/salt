# -*- coding: utf-8 -*-
'''
Management of Porto Containers

Installation Prerequisites

.. code-block:: bash
    porto-py/porto: https://github.com/yandex/porto.git

'''


# Import Python Futures
from __future__ import absolute_import

import io
import json
import logging
import os
import os.path
import pipes
import re
import shutil
import string
import time
import uuid
import base64
import errno
import subprocess
import copy

# Import Salt libs
from salt.exceptions import CommandExecutionError, SaltInvocationError
import salt.ext.six as six
from salt.ext.six.moves import map

# pylint: disable=import-error,redefined-builtin
import salt.utils
import salt.utils.decorators
import salt.utils.files
import salt.utils.thin
import salt.pillar
import salt.exceptions
import salt.fileclient

from salt.state import HighState
import salt.client.ssh.state

# pylint: disable=import-error
try:
    import porto
except ImportError:
    logging.info("Can't import porto-py module")

CLIENT_TIMEOUT = 60

# Define the module's virtual name
__virtualname__ = 'porto'

def __virtual__():
    '''
    Only load if docker libs are present
    '''
    return True

# def _get_client(timeout=None):
def _get_api():
    '''
    Obtains a connection to a porto API

    By default it will use the base porto-py
    '''

    try:
        p_api = porto.Connection(timeout=20)
        p_api.connect()
    except Excetion as exc:
        raise CommandExecutionError(
            'Porto connection failed {0}'.format(exc))

    return p_api


def _porto_client(wrapped):
    '''
    Decorator to run a function that requires the use of a porto.Conncection()
    instance.
    '''
    # @functools.wraps(wrapped)
    def wrapper(*args, **kwargs):
        '''
        Set connection to porto api
        '''
        # client_timeout = __context__.get('docker.timeout', CLIENT_TIMEOUT)
        api = _get_api()
        wrapped(api, *args, **salt.utils.clean_kwargs(**kwargs))
        api.disconnect()
    return wrapper


def state(name):
    '''
    Returns the state of the container

    name
        Container name

    **Return Data**

    A string representing the current state of the container(
    ``running``, ``paused``, ``stopped``, ``busy``)

    CLI Example:

    .. code-block:: bash

        salt myminion porto.state mycontainer
    '''
    api = _get_api()
    state = api.GetData(name, 'state')
    api.disconnect()
    return state
    # return api.getData(name, 'state')


def exists(name):
    '''
    Check if a given container exists

    name
        Container name

    **Return Data**

    A boolean(``True`` if the container exists , otherwise ``False``)

    CLI Example:

    .. code-block:: bash

        salt myminion porto.exists mycontainer
    '''

    api = _get_api()
    list = api.List()
    if name in list:
        api.disconnect()
        return True
    else:
        api.disconnect()
        return False


def create(name,
           **kwargs):
    '''
    Create a new container

    name
        Name of new container

    CLI Example:

    .. code-block:: bash
        salt myminion porto.create mycontainer
    '''

    api = _get_api()
    context = {}
    logging.debug('kwargs: {}'.format(kwargs))
    context = salt.utils.clean_kwargs(**copy.deepcopy(kwargs))
    logging.debug('context: {}'.format(context))

    try:
        api.Create(name)
        set_property(name, context)
    except Exception as exc:
        logging.debug("can't create container {0}".format(exc))
        api.disconnect()
        return False
    api.disconnect()
    return True


def destroy(name):
    '''
    Destroy existing container

    name
        Name of container

    CLI Example:

    .. code-block:: bash
        salt myminion porto.destroy mycontainer
    '''

    api = _get_api()
    try:
        api.Destroy(name)
    except Exception as exc:
        logging.debug("can't destroy container {0}".format(exc))
        api.disconnect()
        return False
    api.disconnect()
    return True


def start(name):
    '''
    Start existing container

    name
        Name of container

    CLI Example:

    .. code-block:: bash
        salt myminion porto.start mycontainer
    '''

    api = _get_api()
    try:
        api.Start(name)
    except Exception as exc:
        logging.debug("can't start container {0}".format(exc))
        api.disconnect()
        return False
    api.disconnect()
    return True


def stop(name):
    '''
    Stop existing container

    name
        Name of container

    CLI Example:

    .. code-block:: bash
        salt myminion porto.stop mycontainer
    '''

    api = _get_api()
    try:
        api.Stop(name)
    except Exception as exc:
        logging.debug("can't stop container {0}".format(exc))
        api.disconnect()
        return False
    api.disconnect()
    return True

def restart(name):
    '''
    Restart a container

    name
        Name of container

    CLI Example:

    .. code-block:: bash
        salt myminion porto.stop mycontainer
    '''

    try:
        start(name)
        stop(name)
    except Exception as exc:
        logging.debug("can't restart container {0}".format(exc))
        return False

    return True

def set_property(name, context):
    api = _get_api()
    for prop, value in context.items():
        logging.debug('try to set property {0}={1}'.format(prop, value))
        try:
            api.SetProperty(name, prop, value)
            logging.debug('set property {0}={1}'.format(prop, value))
        except Exception as exc:
            logging.debug("can't set property ({1}={2}) for container {3}: {0}".format(exc, name,
                                                                                       prop,
                                                                                       value))
            api.disconnect()
            return False

    api.disconnect()
    return True


def run(name,
        cmd):
    '''
    Create and start container

    name
        Name of container

    cmd
        Command to run

    CLI Example:

    .. code-block:: bash
        salt myminion porto.run mycontainer 'sleep 100'
    '''
    context = {'command': cmd}
    try:
        create(name)
        set_property(name, context)
        start(name)
    except Exception as exc:
        logging.debug("can't run container {0}".format(exc))
        return False

    return True


def inspect_container(name):
    '''
    Retrieves container information.

    name
        Container name


    **RETURN DATA**

    A dictionary of container information


    CLI Example:

    .. code-block:: bash

        salt myminion porto.inspect_container mycontainer
    '''

    if exists(name):
        api = _get_api()
        try:
            container = api.Find(name)
            res = container.GetProperties()
            return res
        except Exception as exc:
            logging.debug("can't get container \'{0}\' information {1}".format(name, exc))
            api.disconnect()
            return {}
        api.disconnect()
        return {}
    else:
        return {}
