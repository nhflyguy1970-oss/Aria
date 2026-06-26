# Source Generated with Decompyle++
# File: diff_util.cpython-312.pyc (Python 3.12)

import difflib

def make_diff(original = None, updated = None):
    lines = difflib.unified_diff(original.splitlines(), updated.splitlines(), fromfile = 'original', tofile = 'proposed', lineterm = '')
    return '\n'.join(lines)


def show_diff(original = None, updated = None):
    diff = difflib.unified_diff(original.splitlines(), updated.splitlines(), fromfile = 'original', tofile = 'proposed', lineterm = '')
    print('\n--- DIFF ---\n')
    for line in diff:
        print(line)
    print()

