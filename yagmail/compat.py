import os
import sys

PY3 = sys.version_info[0] == 3
text_type = (str,) if PY3 else (str, unicode)
