"""
This file contains a function that chooses between test and production settings
Useful for when running python scripts that require settings file
"""

import os
import sys
parent_path = os.path.dirname(os.path.realpath(__file__))+'/../'
sys.path.append(parent_path)

def load_settings(sys_argv):
    settings = "util.test_settings"
    try:
        from util.keys.secret_key import ENV
        if ENV == 'production' or ENV == 'staging':
            settings = "util.settings"
    except ImportError:
        settings = "util.test_settings"

    for arg in sys_argv:
        if '--production' == arg:
            settings = "util.settings"
            break
        elif '--test' == arg:
            settings = "util.test_settings"
            break
        elif '--development' == arg:
            settings = "util.test_settings"
        elif '--settings=util.settings' == arg:
            settings = "util.settings"
        elif '--settings=util.test_settings' == arg:
            settings = "util.test_settings"

    import os
    import sys
    parent_path = os.path.dirname(os.path.realpath(__file__))+'/../'
    sys.path.append(parent_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)
    return settings

if __name__ == "__main__":
    print load_settings(sys.argv)
