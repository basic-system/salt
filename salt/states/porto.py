# -*- coding: utf-8 -*-
'''
Managment of Porto containers (https://github.com/yandex/porto.git)

This is the state module to acoompany the :mod:`porto<salt.modules.porto`
execution module.

Porto is a lightweight, portable, self-sufficient software container
wrapper.

This state module requires porto-py () version >= 3.1
'''

from __future__ import absolute_import
import copy
import logging
import sys
import traceback

# Import salt libs
from salt.exceptions import CommandExecutionError, SaltInvocationError
# pylint: disable=no-name-in-module,import-error

import salt.modules.porto


# pylint: enable=no-name-in-module,import-error
import salt.utils
import salt.ext.six as six

# Enable proper logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Define the module's virtual name
__virtualname__ = 'porto'


def __virtual__():
    '''
    Only load if the porto execution module is available
    '''
#     if 'porto.version' in __salt__:
#         global _validate_input  # pylint: disable=global-statement
#         _validate_input = salt.utils.namespaced_function(
#            _validate_input, globals(), preserve_context=True,
#        )
#        return __virtualname__
#    return (False, __salt__.missing_fun_string('porto.version'))
    return True

def running(name,
            image=None,
            start=True,
            **kwargs):
    '''
     Ensure that a container with a specific configuration is present and
     running

    name
        Name of the container

    Usage Examples:

    .. code-block:: yaml
        mycontainer:
            porto.running:
                - hostname: hostname
                - command: "sleep 300"
                ...
    '''

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if __salt__['porto.exists'](name):
        new_container = False
        try:
            pre_config = __salt__['porto.inspect_container'](name)
        except CommandExecutionError as exc:
            ret['comment'] = ('Error occurred checking for existence of '
                              'container \'{0}\': {1}'.format(name, exc))
            logging.debug(ret['comment'])
            return ret
    else:
        new_container = True
        pre_config = {}

    if __opts__['test']:
        if not new_container:
            ret['result'] = True
            ret['comment'] = (
                'Container \'{0}\' is already configured as specified'
                .format(name)
            )
            logging.debug(ret['comment'])
        else:
            ret['result'] = None
            ret['comment'] = 'Container \'{0}\' will be '.format(name)
            ret['comment'] += 'created'
            # ret['comment'] += 'created' if not pre_config else 'replaced'
        return ret

    if 'cmd' in kwargs:
        kwargs['command'] = kwargs.pop('cmd')

    create_kwargs = salt.utils.clean_kwargs(**copy.deepcopy(kwargs))

    logging.debug("C name is: {}; new_container is {}, pre_config is {}".format(name, new_container, pre_config))

    if not pre_config:
        logging.debug('pre_config is set')
        new_container = True

    if new_container:
        res = __salt__['porto.create'](name, **create_kwargs)
        if res:
            res = __salt__['porto.start'](name)
            ret['result'] = res
            return ret
        else:
            ret['comment'] = 'Can\'t create container \'{0}\': {1}'.format(name. res)
            return ret
    else:
        changes_needed = False
        for prop, value in create_kwargs.items():
            if pre_config[prop] != value:
                logging.debug("prop {} not the same ({} {})".format(prop, pre_config[prop], value))
                changes_needed = True

        if changes_needed:
            if __salt__['porto.state'] == 'running':
                res = __salt__['porto.stop'](name)
                if not res:
                    ret['comment'] = 'Can\'t stop container \'{0}\' for change prop'.format(name)
                    return ret

            res = __salt__['porto.set_property'](name, create_kwargs)
            if not res:
                ret['comment'] = 'Can\'t set property \'{0}\''.format(name)
                return ret

            res = __salt__['porto.start'](name)
            if not res:
                ret['comment'] = 'Can\'t start \'{0}\''.format(name)
                return ret

            ret['result'] = True
        else:
            logging.debug('Changes not needed')
            state = __salt__['porto.state'](name)
            logging.debug('current state is {0}'.format(state))
            if state == 'running':
                ret['result'] = True
                ret['comment'] = 'service already running'
                return ret
            else:
                if state == 'dead': # Porto can't start dead container
                    logging.debug('Container is dead; Try to stop container')
                    res = __salt__['porto.stop'](name)
                    if not res:
                        ret['comment'] = 'Can\'t stop container \'{0}\''.format(name)
                        return ret

                res = __salt__['porto.start'](name)
                if not res:
                    ret['comment'] = 'Can\'t start \'{0}\''.format(name)
                    return ret
                ret['result'] = True
                return ret

    return ret


def absent(name):
    '''
    Ensure that a container is absent

    name
        Name of the container

    Usage Examples:

    .. code-block:: yaml
        mycontainer:
            porto.absent

        multiple_containers:
            porto.absent:
                - names:
                    - foo
                    - bar
                    - baz
    '''

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if not __salt__['porto.exists'](name):
        ret['result'] = True
        ret['comment'] = 'Container \'{0}\' does not exist'.format(name)
        return ret

    pre_state = __salt__['porto.state'](name)

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Container \'{0}\' will be removed'.format(name)
        return ret

    try:
        ret['changes']['removed'] = __salt__['porto.destroy'](name)
    except Exception as exc:
        ret['comment'] = 'Failed to remove container \'{0}\': {1}'.format(name, exc)
        return ret

    if __salt__['porto.exists'](name):
        ret['comment'] = 'Failed to remove container \'{0}\''.format(name)
    else:
        ret['comment'] = 'Removed container \'{0}\''.format(name)
        ret['result'] = True
    return ret
