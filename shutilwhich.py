# -*- coding: utf-8 -*-

import shutil

if not hasattr(shutil, 'which'):
    import os
    import sys

    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        """
        Everything below this point has been copied verbatim from
        the Python-3.3 sources. See: https://github.com/mbr/shutilwhich

        :param cmd: The command to search for.
        :param mode: The file-access mode.
        :param path: Optional path to search under.
        :return: The path to the command, or None if not found.
        """
        def _access_check(fn, access_mode):
            return os.path.exists(fn) \
                   and os.access(fn, access_mode) \
                   and not os.path.isdir(fn)

        if _access_check(cmd, mode):
            return cmd

        path = (path or os.environ.get('PATH', os.defpath)).split(os.pathsep)

        if sys.platform == 'win32':
            if path not in os.curdir:
                path.insert(0, os.curdir)

            pathext = os.environ.get('PATHEXT', '').split(os.pathsep)
            matches = [cmd for ext in pathext if
                       cmd.lower().endswith(ext.lower())]
            files = [cmd] if matches \
                else [cmd + ext.lower() for ext in pathext]
        else:
            files = [cmd]

        seen = set()
        for directory in path:
            directory = os.path.normcase(directory)
            if directory not in seen:
                seen.add(directory)
                for thefile in files:
                    name = os.path.join(directory, thefile)
                    if _access_check(name, mode):
                        return name
        return None

    shutil.which = which
