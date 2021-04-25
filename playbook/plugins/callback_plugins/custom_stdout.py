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

from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback.yaml import CallbackModule as Yaml
from ansible.utils.display import Display as DefaultDisplay
from ansible.utils.color import stringc, colorize, hostcolor


class BaseElement():
    def __init__(self):
        self._children = []
        self._msg = {"content": '', "stderr": False, "newline": True}

    def addChild(self, child):
        self._children.append(child)

    def _display(self, msg="", stderr=False, newline=True):
        if stderr:
            fileObj = sys.stderr
        else:
            fileObj = sys.stdout

        outMsg = msg.strip()

        if newline:
            outMsg += '\n'

        fileObj.write(outMsg)
        try:
            fileObj.flush()
        except IOError as e:
            if e.errno != errno.EPIPE:
                raise

    def setMessage(self, msg="", stderr=False, newline=True):
        self._msg["content"] = msg
        self._msg["stderr"] = stderr
        self._msg["newline"] = newline

    def printToScreen(self):
        self._display(self._msg["content"], self._msg["stderr"], self._msg["newline"])
        for child in self._children:
            child.printToScreen()

    def clearScreen(self):
        sys.stdout.write("\x1b[1A\x1b[2K") # move up cursor and delete whole line
        for child in self._children:
            child.clearScreen()

class DisplayPlaybook(BaseElement):
    def __init__(self):
        super(DisplayPlaybook, self).__init__()
        self._play = DisplayPlay()
        self.addChild(self._play)

class DisplayPlay(BaseElement):
    def __init__(self):
        super(DisplayPlay, self).__init__()
        self._task = DisplayTask()
        self.addChild(self._task)

class DisplayTask(BaseElement):
    def __init__(self):
        super(DisplayTask, self).__init__()
        self._hosts = {}

    def addHostMessage(self, host_name, host_message):
        if host_name in self._hosts:
            self._hosts[host_name].setMessage("[%s] %s" % (host_name, host_message))
        else:
            self._hosts[host_name] = DisplayHost()
            self._hosts[host_name].setMessage("[%s] %s" % (host_name, host_message))
            self.addChild(self._hosts[host_name])

class DisplayHost(BaseElement):
    def __init__(self):
        super(DisplayHost, self).__init__()


class CustomDisplay(DefaultDisplay):
    def __init__(self):
        super(CustomDisplay, self).__init__()

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=False):
        nocolor = msg

        # for logging to file
        super(CustomDisplay, self).display(msg=msg, color=color, stderr=color, screen_only=False, log_only=True, newline=True)


    def displayBanner(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=True):
        msg = to_text(msg)

        self.displayToScreen(u"\n%s" % (msg), color=color)


    def displayToScreen(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=True):

        has_newline = msg.endswith(u'\n')
        if has_newline:
            msg2 = msg[:-1]
        else:
            msg2 = msg

        if color:
            msg2 = stringc(msg2, color)

        if has_newline or newline:
            msg2 = msg2 + u'\n'

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

    def v2_playbook_on_start(self, playbook):
        super(CallbackModule, self).v2_playbook_on_start(playbook)

        from os.path import basename
        self._display_playbook = DisplayPlaybook()
        self._display_playbook.setMessage(u"Playbook: %s" % basename(playbook._file_name))
        self._display_playbook.printToScreen()

    def v2_playbook_on_play_start(self, play):
        super(CallbackModule, self).v2_playbook_on_play_start(play)
        self._display_playbook.clearScreen()
        self._display_playbook._play.setMessage(u"Play: %s" % play.get_name().strip())
        self._display_playbook.printToScreen()

    def v2_playbook_on_task_start(self, task, is_conditional):
        super(CallbackModule, self).v2_playbook_on_task_start(task, is_conditional)
        self._display_playbook.clearScreen()
        self._display_playbook._play._task.setMessage(u"Task: %s" % task.get_name().strip())
        self._display_playbook.printToScreen()

    def v2_runner_on_start(self, host, task):
        super(CallbackModule, self).v2_runner_on_start(host, task)

        self._display_playbook.clearScreen()
        self._display_playbook._play._task.addHostMessage(u"%s" % host, "STARTED!")
        self._display_playbook.printToScreen()

    def v2_runner_on_ok(self, result):
        super(CallbackModule, self).v2_runner_on_ok(result)

        self._display_playbook.clearScreen()
        delegated_vars = delegated_vars = result._result.get('_ansible_delegated_vars', None)
        msg = ''
        if delegated_vars:
            msg += "-> %s " % delegated_vars['ansible_host']
        if result._result.get('changed', False):
            msg += "CHANGED!"
        else:
            msg += "OK!"
        self._display_playbook._play._task.addHostMessage(result._host.get_name(), msg)

        self._display_playbook.printToScreen()

    def v2_runner_on_failed(self, result, ignore_errors=False):
        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        self._display_playbook.clearScreen()
        delegated_vars = delegated_vars = result._result.get('_ansible_delegated_vars', None)
        msg = ''
        if delegated_vars:
            msg += "-> %s " % delegated_vars['ansible_host']
        msg += "Failed!"
        self._display_playbook._play._task.addHostMessage(result._host.get_name(), msg)
        self._display_playbook.printToScreen()

    def v2_runner_on_skipped(self, result):
        super(CallbackModule, self).v2_runner_on_skipped(result)

        self._display_playbook.clearScreen()
        delegated_vars = delegated_vars = result._result.get('_ansible_delegated_vars', None)
        msg = ''
        if delegated_vars:
            msg += "-> %s " % delegated_vars['ansible_host']
        msg += "Skipped!"
        self._display_playbook._play._task.addHostMessage(result._host.get_name(), msg)
        self._display_playbook.printToScreen()

    def v2_runner_on_unreachable(self, result):
        super(CallbackModule, self).v2_runner_on_unreachable(result)

        self._display_playbook.clearScreen()
        delegated_vars = delegated_vars = result._result.get('_ansible_delegated_vars', None)
        msg = ''
        if delegated_vars:
            msg += "-> %s " % delegated_vars['ansible_host']
        msg += "Unreachable!"
        self._display_playbook._play._task.addHostMessage(result._host.get_name(), msg)
        self._display_playbook.printToScreen()

    def v2_runner_on_async_poll(self, result):
        super(CallbackModule, self).v2_runner_on_async_poll(result)

    def v2_playbook_on_stats(self, stats):
        super(CallbackModule, self).v2_playbook_on_stats(stats)

        self._display.displayBanner("RECAP")
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.displayToScreen(
                u"%s : %s %s %s %s %s %s %s" % (
                    hostcolor(h, t),
                    colorize(u'ok', t['ok'], C.COLOR_OK),
                    colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                    colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                    colorize(u'failed', t['failures'], C.COLOR_ERROR),
                    colorize(u'skipped', t['skipped'], C.COLOR_SKIP),
                    colorize(u'rescued', t['rescued'], C.COLOR_OK),
                    colorize(u'ignored', t['ignored'], C.COLOR_WARN),
                )
            )

#     def v2_playbook_on_play_notify(self, play):
#         super(CallbackModule, self).v2_playbook_on_play_notify(play)
# 
#     def v2_playbook_on_play_no_hosts_matched(self, play):
#         super(CallbackModule, self).v2_playbook_on_play_no_hosts_matched(play)
# 
#     def v2_playbook_on_play_no_hosts_remaining(self, play):
#         super(CallbackModule, self).v2_playbook_on_play_no_hosts_remaining(play)


    # enable verbosity for logging (file logging)
    def _run_is_verbose(self, result, verbosity=0):
        return True
