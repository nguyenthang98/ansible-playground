from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: custom_stdout
    type: stdout
    short_description: customized Ansible screen output
    version_added: 2.9
    description:
        - Customized stdout for more informative
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout in configuration
'''

import sys

from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback.yaml import CallbackModule as Yaml
from ansible.utils.display import Display as DefaultDisplay
from ansible.utils.color import stringc

class CustomDisplay(DefaultDisplay):
    def __init__(self):
        super(CustomDisplay, self).__init__()

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=False):
        nocolor = msg

        # for logging to file
        super(CustomDisplay, self).display(msg=msg, color=color, stderr=color, screen_only=False, log_only=True, newline=True)

        if not log_only:

            has_newline = msg.endswith(u'\n')
            if has_newline:
                msg2 = msg[:-1]
            else:
                msg2 = msg

            if color:
                msg2 = stringc(msg2, color)

            if has_newline or newline:
                msg2 = msg2 + u'\n'
            else:
                msg2 = msg2.replace(u'\n', u'\r')

            msg2 = to_bytes(msg2, encoding=self._output_encoding(stderr=stderr))
            if sys.version_info >= (3,):
                msg2 = to_text(msg2, self._output_encoding(stderr=stderr), errors='replace')

            if not stderr:
                fileobj = sys.stdout
            else:
                fileobj = sys.stderr

            fileobj.write(msg2)

            try:
                fileobj.flush()
            except IOError as e:
                if e.errno != errno.EPIPE:
                    raise

class CallbackModule(Yaml):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'custom_stdout'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self._display = CustomDisplay()


    def v2_playbook_on_play_start(self, play):
        super(CallbackModule, self).v2_playbook_on_play_start(play)
