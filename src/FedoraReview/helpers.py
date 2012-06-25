#-*- coding: utf-8 -*-

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# (C) 2011 - Tim Lauridsen <timlau@fedoraproject.org>

'''
Tools for helping Fedora package reviewers
'''

import logging
import os.path
import re
import urllib
from subprocess import call, Popen, PIPE

from settings import Settings
from review_error import FedoraReviewError

class Helpers(object):

    def __init__(self):
        self.log = Settings.get_logger()

    def _run_cmd(self, cmd):
        self.log.debug('Run command: %s' % cmd)
        cmd = cmd.split(' ')
        try:
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
            output, error = proc.communicate()
        except OSError, e:
            self.log.debug("OS error", exc_info=True)
            self.log.error("OS error running " + cmd, str(e))
        return output

    def _md5sum(self, file):
        ''' get the md5sum for a file

        :arg file: the file to get the the md5sum for
        :return: md5sum
        '''
        cmd = "md5sum %s" % file
        out = self._run_cmd(cmd)
        words = out.split(' ', 1)
        if len(words) == 2:
            return words[0]
        else:
            raise FedoraReviewError("Bad md5sum output: " + out)

    def _get_file(self, link, directory, logger=None):
        fname = os.path.basename(link)
        path = os.path.join(directory, fname)
        if os.path.exists(path) and Settings.cache:
             if logger:
                 logger(True)
             logging.debug('Using cached source: ' + fname)
             return  path
        self.log.debug("  --> %s : %s" % (directory, link))
        if logger:
           logger(False)
        try:
            file, headers = urllib.urlretrieve(link, path)
        except IOError, err:
            raise FedoraReviewError('Getting error "%s" while trying'
                                    ' to write file: %s' % (err, path))
        return path if os.path.exists(path) else None

    @staticmethod
    def rpmdev_extract(archive, extract_dir):
        """
        Unpack archive in extract_dir. Returns true if
        from subprocess.call() returns 0
        """
        cmd = 'rpmdev-extract -qC ' + extract_dir + ' ' + archive
        cmd += ' &>/dev/null'
        rc = call(cmd, shell=True)
        if rc != 0:
            Settings.get_logger().debug("Cannot unpack "  + archive)
        return rc == 0

    @staticmethod
    def check_rpmlint_errors(out, log):
        """ Check the rpmlint output, return(ok, errmsg)
        If ok, output is OK and there is 0 warnings/errors
        If not ok, and errmsg!= None there is system errors,
        reflected in errmsg. If not ok and sg == None parsing
        is ok but there are warnings/errors"""

        problems = re.compile('(\d+)\serrors\,\s(\d+)\swarnings')
        lines = out.split('\n')[:-1]
        err_lines = filter( lambda l: l.lower().find('error') != -1,
                            lines)
        if len(err_lines) == 0:
            Settings.get_logger().debug('Cannot parse rpmlint output: '
                                         + out)
            return False, 'Cannot parse rpmlint output:'

        res = problems.search(err_lines[-1])
        if res and len(res.groups()) == 2:
            errors, warnings = res.groups()
            if errors == '0' and warnings == '0':
                return True, None
            else:
                return False, None
        else:
            log.debug('Cannot parse rpmlint output: ' + out )
            return False, 'Cannot parse rpmlint output:'


# vim: set expandtab: ts=4:sw=4:
