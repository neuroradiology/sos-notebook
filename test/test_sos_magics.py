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

import os
import sys
import unittest
from ipykernel.tests.utils import execute, wait_for_idle
from sos_notebook.test_utils import sos_kernel, get_display_data, get_std_output

class TestSoSMagics(unittest.TestCase):
    def testHelp(self):
        '''Test help messages'''
        with sos_kernel() as kc:
            # create a data frame
            execute(kc=kc, code='\n'.join('%{} -h'.format(magic) for magic in (
                'cd', 'debug', 'dict', 'get', 'matplotlib', 'paste', 'preview',
                'put', 'render', 'rerun', 'run', 'save', 'sandbox', 'set',
                'sessioninfo', 'sosrun', 'sossave', 'shutdown', 'taskinfo', 'tasks',
                'toc', 'use', 'with', 'pull', 'push')))
            wait_for_idle(kc)

    def testMagicConnectInfo(self):
        '''Test connect info'''
        with sos_kernel() as kc:
            # create a data frame
            execute(kc=kc, code='%connectinfo')
            wait_for_idle(kc)

    def testMagicMatplotlib(self):
        with sos_kernel() as kc:
            # create a data frame
            execute(kc=kc, code='''
%matplotlib inline
In [59]:
import matplotlib.pyplot as plt
import numpy as np
x = np.linspace(0, 10)
plt.plot(x, np.sin(x), '--', linewidth=2)
plt.show()''')
            wait_for_idle(kc)


    def testMagicSave(self):
        with sos_kernel() as kc:
            if os.path.isfile('test.txt'):
                os.remove('test.txt')
            execute(kc=kc, code='''
%preview ~/test.txt
%save ~/test.txt
a=1
''')
            wait_for_idle(kc)
            with open(os.path.join(os.path.expanduser('~'), 'test.txt')) as tt:
                self.assertEqual(tt.read(), 'a=1\n')

    def testMagicSoSSave(self):
        with sos_kernel() as kc:
            execute(kc=kc, code='''
%frontend --cell 0 --workflow --default-kernel SoS --cell-kernel SoS --filename ~/test.ipynb
%sossave ~/test.sos
[10]
a=1
''')
            wait_for_idle(kc)
            execute(kc=kc, code='''
%frontend --cell 0 --workflow --default-kernel SoS --cell-kernel SoS --filename ~/test1
%sossave --to sos
[10]
a=1
''')
            wait_for_idle(kc)
            self.assertTrue(os.path.exists(os.path.join(os.path.expanduser('~'), 'test1.sos')))

    def testMagicPreview(self):
        with sos_kernel() as kc:
            # preview variable
            iopub = kc.iopub_channel
            execute(kc=kc, code='''
%preview -n a
a=1
''')
            _, stderr = get_std_output(iopub)
            self.assertEqual(stderr, '')

            # preview csv file
            execute(kc=kc, code='''
%preview a.csv
with open('a.csv', 'w') as csv:
    csv.write("""\
a,b,c
1,2,3
4,5,6
""")
''')
            res = get_display_data(iopub, 'text/html')
            self.assertTrue('dataframe_container' in res, 'Expect preview {}'.format(res))
            # preview txt file
            execute(kc=kc, code='''
%preview a.txt
with open('a.txt', 'w') as txt:
    txt.write("""\
hello
world
""")
''')
            stdout, stderr = get_std_output(iopub)
            self.assertEqual(stderr, '')
            self.assertTrue('world' in stdout, 'Expect preview {}'.format(stdout))
            # preview zip
            execute(kc=kc, code='''
%preview -n a.zip
import zipfile

with zipfile.ZipFile('a.zip', 'w') as zfile:
    zfile.write('a.csv')
''')
            stdout, stderr = get_std_output(iopub)
            self.assertEqual(stderr, '')
            self.assertTrue('a.csv' in stdout, 'Expect preview {}'.format(stdout))
            # preview tar
            execute(kc=kc, code='''
%preview -n a.tar
import tarfile

with tarfile.open('a.tar', 'w') as tar:
    tar.add('a.csv')

''')
            stdout, stderr = get_std_output(iopub)
            self.assertEqual(stderr, '')
            self.assertTrue('a.csv' in stdout, 'Expect preview {}'.format(stdout))
            # preview tar.gz
            execute(kc=kc, code='''
%preview -n a.tar.gz
import tarfile

with tarfile.open('a.tar.gz', 'w:gz') as tar:
    tar.add('a.csv')
''')
            stdout, stderr = get_std_output(iopub)
            self.assertEqual(stderr, '')
            self.assertTrue('a.csv' in stdout, 'Expect preview {}'.format(stdout))
            #
            # preview regular .gz
            execute(kc=kc, code='''
%preview -n a.gz
import gzip

with gzip.open('a.gz', 'w') as gz:
    gz.write(b"""
Hello
world
""")
''')
            stdout, stderr = get_std_output(iopub)
            self.assertEqual(stderr, '')
            self.assertTrue('world' in stdout, 'Expect preview {}'.format(stdout))
            # preview md
            execute(kc=kc, code='''
%preview -n a.md
with open('a.md', 'w') as md:
    md.write("""\
# title

* item
* item
""")
''')
            res = get_display_data(iopub, 'text/html')
            self.assertTrue('<li>item</li>' in res, 'Expect preview {}'.format(res))
            # preview html
            execute(kc=kc, code='''
%preview -n a.html
with open('a.html', 'w') as dot:
    dot.write("""\
<!DOCTYPE html>
<html>
<body>

<h1>My First Heading</h1>

<p>My first paragraph.</p>

</body>
</html>
""")
''')
            res = get_display_data(iopub, 'text/html')
            # preview dot, needs imagemagick, which is unavailable under windows.
            if sys.platform == 'win32':
                return
            execute(kc=kc, code='''
%preview -n a.dot
with open('a.dot', 'w') as dot:
    dot.write("""\
graph graphname {
     a -- b -- c;
     b -- d;
}
""")
''')
            res = get_display_data(iopub, 'image/png')
            self.assertGreater(len(res), 1000, 'Expect a image {}'.format(res))

    def testMagicSet(self):
        # test preview of remote file
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            # preview variable
            execute(kc=kc, code='''
%set
%set -v2
%set
%set -v1
''')
        stdout, stderr = get_std_output(iopub)
        self.assertEqual(stderr, '', 'Got {}'.format(stderr))
        self.assertTrue('set' in stdout, 'Got {}'.format(stdout))


    @unittest.skipIf(sys.platform == 'win32', 'AppVeyor does not support linux based docker')
    def testMagicRemotePreview(self):
        # test preview of remote file
        with sos_kernel() as kc:
            iopub = kc.iopub_channel
            # preview variable
            execute(kc=kc, code='''
%preview -n abc.txt -c ~/docker.yml -r docker
%run -r docker -c ~/docker.yml
run:
   echo abc > abc.txt
''')
        stdout, _ = get_std_output(iopub)
        #self.assertEqual(stderr, '', 'Got error {}'.format(stderr))
        self.assertTrue('abc' in stdout, 'Got stdout "{}"'.format(stdout))

    def testMagicSandbox(self):
        with sos_kernel() as kc:
            # preview variable
            execute(kc=kc, code='''
%sandbox
with open('test_blah.txt', 'w') as tb:
    tb.write('a')
''')
            wait_for_idle(kc)
            self.assertFalse(os.path.exists('test_blah.txt'))

    def testMagicDebug(self):
        with sos_kernel() as kc:
            # preview variable
            execute(kc=kc, code='''
%debug on
%debug off
''')
            wait_for_idle(kc)

    def testMagicSessioninfo(self):
        with sos_kernel() as kc:
            # preview variable
            execute(kc=kc, code='''
%use Python3
%use SoS
%sessioninfo
''')
            wait_for_idle(kc)

    def testMagicRender(self):
        with sos_kernel() as kc:
            # preview variable
            execute(kc=kc, code='''
%render
"""
# header

* item1
* item2
"""
''')
            wait_for_idle(kc)

if __name__ == '__main__':
    unittest.main()
