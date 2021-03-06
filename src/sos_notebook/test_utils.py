#!/usr/bin/env python3
#
# This file is part of Script of Scripts (SoS), a workflow system
# for the execution of commands and scripts in different languages.
# Please visit https://github.com/vatlab/SOS for more information.
#
# Copyright (C) 2016 Bo Peng (bpeng@mdanderson.org)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

#
# NOTE: for some namespace reason, this test can only be tested using
# nose.
#
# % nosetests test_kernel.py
#
#
from contextlib import contextmanager
from ipykernel.tests.utils import start_new_kernel, assemble_output


import atexit
from queue import Empty
KM = None
KC = None


@contextmanager
def sos_kernel():
    """Context manager for the global kernel instance
    Should be used for most kernel tests
    Returns
    -------
    kernel_client: connected KernelClient instance
    """
    yield start_sos_kernel()


def flush_channels(kc=None):
    """flush any messages waiting on the queue"""

    if kc is None:
        kc = KC
    for channel in (kc.shell_channel, kc.iopub_channel):
        while True:
            try:
                channel.get_msg(block=True, timeout=0.1)
            except Empty:
                break
            # do not validate message because SoS has special sos_comm
            #else:
            #    validate_message(msg)

def start_sos_kernel():
    """start the global kernel (if it isn't running) and return its client"""
    global KM, KC
    if KM is None:
        KM, KC = start_new_kernel(kernel_name='sos')
        atexit.register(stop_sos_kernel)
    else:
        flush_channels(KC)
    return KC

def stop_sos_kernel():
    """Stop the global shared kernel instance, if it exists"""
    global KM, KC
    KC.stop_channels()
    KC = None
    if KM is None:
        return
    KM.shutdown_kernel(now=False)
    KM = None

def get_result(iopub):
    """retrieve result from an execution"""
    result = None
    while True:
        msg = iopub.get_msg(block=True, timeout=1)
        msg_type = msg['msg_type']
        content = msg['content']
        if msg_type == 'status' and content['execution_state'] == 'idle':
            # idle message signals end of output
            break
        elif msg['msg_type'] == 'execute_result':
            result = content['data']
        elif msg['msg_type'] == 'display_data':
            result = content['data']
        else:
            # other output, ignored
            pass
    # text/plain can have fronzen dict, this is ok,
    from numpy import array, matrix, uint8
    # suppress pyflakes warning
    array
    matrix
    # it can also have dict_keys, we will have to redefine it
    def dict_keys(args):
        return args
    if result is None:
        return None
    else:
        return eval(result['text/plain'])

def get_display_data(iopub, data_type='text/plain'):
    """retrieve display_data from an execution from subkernel
    because subkernel (for example irkernel) does not return
    execution_result
    """
    result = None
    while True:
        msg = iopub.get_msg(block=True, timeout=1)
        msg_type = msg['msg_type']
        content = msg['content']
        if msg_type == 'status' and content['execution_state'] == 'idle':
            # idle message signals end of output
            break
        elif msg['msg_type'] == 'display_data':
            if isinstance(data_type, str):
                if data_type in content['data']:
                    result = content['data'][data_type]
            else:
                for dt in data_type:
                    if dt in content['data']:
                        result = content['data'][dt]
        # some early version of IRKernel still passes execute_result
        elif msg['msg_type'] == 'execute_result':
            result = content['data']['text/plain']
    return result

def clear_channels(iopub):
    """assemble stdout/err from an execution"""
    while True:
        msg = iopub.get_msg(block=True, timeout=1)
        msg_type = msg['msg_type']
        content = msg['content']
        if msg_type == 'status' and content['execution_state'] == 'idle':
            # idle message signals end of output
            break

def get_std_output(iopub):
    '''Obtain stderr and remove some unnecessary warning from 
    https://github.com/jupyter/jupyter_client/pull/201#issuecomment-314269710'''
    stdout, stderr = assemble_output(iopub)
    return stdout, '\n'.join([x for x in stderr.splitlines() if 'sticky' not in x and 'RuntimeWarning' not in x and 'communicator' not in x])
