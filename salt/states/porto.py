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
     runnning

    name
        Name of the container

    Usage Examples:

    .. code-block:: yaml
        mycontainer:
            porto.runnning:
                - hostname: hostname
                - command: "sleep 300"
                ...
    '''

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    if 'cmd' in kwargs:
        kwagrs['command'] = kwargs.pop('cmd')

    if __opts__['test']:
        if not new_container:
            ret['result'] = True
            ret['comment'] = (
                'Container \'{0}\' is already configured as specified'
                .format(name)
            )
        else:
            ret['result'] = None
            ret['comment'] = 'Container \'{0}\' will be '.format(name)
            ret['comment'] += 'created'
            # ret['comment'] += 'created' if not pre_config else 'replaced'
        return ret

    comments = []
    create_kwargs = salt.utils.clean_kwargs(**copy.deepcopy(kwargs))
    logging.debug("C name is: {}".format(name))
    res = __salt__['porto.create'](name, **create_kwargs)
    if res:
        res = __salt__['porto.start'](name)

    ret['result'] = res

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
