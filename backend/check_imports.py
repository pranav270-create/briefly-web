"""
This script checks for external Python dependencies in a given directory.
"""

import os
import ast
import sys


def get_imports(file_path):
    with open(file_path, 'r') as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if '.' not in alias.name:  # Exclude file imports
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ''
            if '.' not in module:  # Exclude file imports
                for alias in node.names:
                    imports.add(f"{module}.{alias.name}" if module else alias.name)

    return imports


def get_all_dependencies(root_dir):
    all_dependencies = set()

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                all_dependencies.update(get_imports(file_path))

    # Filter out built-in modules
    return {dep for dep in all_dependencies if dep not in sys.builtin_module_names}


if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    dependencies = get_all_dependencies(root_dir)

    print("External Python dependencies found:")
    for dep in sorted(dependencies):
        print(dep)
