# -*- coding: utf-8 -*-

import os
import platform
import re
import shutil
import sublime
import sublime_plugin
import subprocess
import sys
import tempfile

PY_VERSION = sys.version_info[0]
OS_PLATFORM = platform.system()

PLUGIN_PATH = os.path.abspath(os.path.dirname(__file__))
PLUGIN_NAME = 'Php Tidy'


# if 3 == PY_VERSION:
#     # python3 and st3
#     from . import shutilwhich
# else:
#     # python2 and st2
#     import shutilwhich


class PhpTidyCommand(sublime_plugin.TextCommand):
    temp_file_path = None
    temp_file_name = None
    tidy_path = None
    temp_dir = None
    tidy_bkup_file_path = None
    tidy_cache_file_path = None

    def run(self, edit):
        view = self.view

        # ensure php in path
        php_path = shutil.which('php')
        if php_path is None:
            sublime.error_message(
                '%s Error\n\n'
                'PHP must be installed and added to your\n'
                'environment PATH variable in order to use\n'
                'this plug-in.' % PLUGIN_NAME)
            return

        # esnure php tidy script (allman.php)
        self.tidy_path = os.path.join(PLUGIN_PATH, 'allman.php')
        if not os.path.exists(self.tidy_path):
            sublime.error_message(
                '%s Error\n\n'
                'Tidy script missing.\n\n'
                '%s' % (PLUGIN_NAME, self.tidy_path))
            return

        # remember the current viewport position
        cur_point = view.sel()[0].a
        y = view.text_to_layout(cur_point)[1]
        x = view.viewport_position()[0]

        # configure paths
        self.temp_file_path = self._save_view_in_temp_file(view)
        self.temp_file_name = os.path.basename(self.temp_file_path)
        self.temp_dir = os.path.dirname(os.path.realpath(self.temp_file_path))
        self.tidy_bkup_file_path = os.path.normpath(os.path.join(
            self.temp_dir, '.' + self.temp_file_name + '.phptidybak~'))
        self.tidy_cache_file_path = os.path.join(
            self.temp_dir, '.phptidy-cache')

        startupinfo = None
        if OS_PLATFORM == 'Windows':
            # prevents command prompt from displaying on windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # run php tidy on the tmp file
        proc = subprocess.Popen([
            php_path, self.tidy_path, 'replace', self.temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            startupinfo=startupinfo,
            cwd=self.temp_dir)

        # any output from process indicates an error occurred
        stdout = proc.communicate(input=None)[0]
        if stdout:
            sublime.error_message(
                '%s Error\n\n'
                '%s' % (PLUGIN_NAME, stdout.decode('utf-8')))
            self._clean_up()
            return

        # ensure tidy content file
        if not os.path.exists(self.temp_file_path):
            sublime.error_message(
                '%s Error\n\n'
                'Fixed PHP temp file missing.\n\n'
                '%s' % (PLUGIN_NAME, self.temp_file_path))
            self._clean_up()
            return

        # read tidy content file
        fh = open(self.temp_file_path, 'rb')
        fixed = fh.read().decode('utf-8')
        fh.close()

        # normalize line endings (unix/lf)
        fixed = fixed.replace('\r\n', '\n').replace('\r', '\n')

        self._clean_up()

        # check for changes in the source and update view
        if fixed != self.source:
            view.replace(edit, self.replace_region, fixed)
            # scroll viewport to the top of previous position
            sublime.set_timeout(lambda: view.set_viewport_position(
                (x, y - 1.0 * view.line_height())), 0)
            # update status bar
            sublime.set_timeout(lambda: sublime.status_message(
                PLUGIN_NAME + ': code fixed.'), 0)
        else:
            # source text same as fixed text...
            sublime.set_timeout(lambda: sublime.status_message(
                PLUGIN_NAME + ': nothing to fix.'), 0)

    def _save_view_in_temp_file(self, view):
        # read buffer contents
        self.replace_region = sublime.Region(0, view.size())
        self.source = view.substr(self.replace_region)

        # create the temp file
        tf = tempfile.NamedTemporaryFile(
            mode='wb', suffix='.php', delete=False)
        tf.write(self.source.encode('utf-8'))
        tf.close()

        # returns the full path to the temp file
        return tf.name

    def _clean_up(self):
        # delete tmp files
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        if os.path.exists(self.tidy_bkup_file_path):
            os.remove(self.tidy_bkup_file_path)
        if os.path.exists(self.tidy_cache_file_path):
            os.remove(self.tidy_cache_file_path)

    def is_enabled(self):
        return True if re.search(
            'php', self.view.settings().get('syntax'),
            re.IGNORECASE) else False
