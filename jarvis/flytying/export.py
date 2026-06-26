# Source Generated with Decompyle++
# File: export.cpython-312.pyc (Python 3.12)

'''Export fly-tying recipes as markdown or plain text.'''
from __future__ import annotations
from typing import Any

def export_recipe(recipe = None, *, fmt):
    if not recipe.get('name'):
        recipe.get('name')
        if not recipe.get('fly_name'):
            recipe.get('fly_name')
    name = str('Pattern')
    lines = []
    if fmt == 'markdown':
        lines.append(f'''# {name}''')
        lines.append('')
        if recipe.get('type'):
            lines.append(f'''**Type:** {recipe['type']}''')
        if recipe.get('hook'):
            lines.append(f'''**Hook:** {recipe['hook']}''')
        if not recipe.get('materials'):
            recipe.get('materials')
        mats = []
        if mats:
            lines.append('')
            lines.append('## Materials')
            (lambda .0: pass# WARNING: Decompyle incomplete
)(mats())
        if not recipe.get('steps'):
            recipe.get('steps')
        steps = []
        if steps:
            lines.append('')
            lines.append('## Steps')
            (lambda .0: pass# WARNING: Decompyle incomplete
)(enumerate(steps, 1)())
    return '\n'.join(lines).strip() + '\n'


def compare_recipes(recipes = None):
    blocks = []
    for r in recipes:
        blocks.append(export_recipe(r, fmt = 'markdown'))
        blocks.append('---')
    return '\n'.join(blocks).rstrip('---\n')

