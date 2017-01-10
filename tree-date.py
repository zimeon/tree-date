#!/usr/bin/env python
"""Print tree of files/dirs showing summary of ages.

Idea is to truncate tree to give a summary of areas of a filesystem
with changes more recent than a certain maximum age.
"""
import os
import os.path
import re
import sys
import time

now = time.time()
max_age = 365

class Node(object):

    def __init__(self, name=None, age=None, num_files=0, parent=None):
        self.name = name
        self.age = age
        self.num_files = num_files
        self.parent = parent
        self.children = []

    def add_child(self, node):
        node.parent = self
        self.children.append(node)
        return(node)

    def add(self, node):
        """Treating node.name as a filepath, add node to tree."""
        n = self
        while (os.path.commonprefix([n.name, node.name]) != n.name):
            n = n.parent
            if (n is None):
                raise Exception("Failed to find parent for %s" % (node.name))
        return(n.add_child(node))

    def preorder(self, visit):
        """Pre-order depth-first traversal of tree.

        Calls visit(node) on each node.
        """
        visit(self)
        for node in self.children:
            node.preorder(visit)

    def postorder(self, visit):
        """Post-order depth-first traversal of tree.

        Calls visit(node) on each node.
        """
        for node in self.children:
            node.postorder(visit)
        visit(self)

    def __str__(self):
        if (self.age is None):
            age_str = 'UNKNOWN AGE'
        elif (self.age == max_age):
            age_str = '>=' + str(self.age) + ' days old'
        else:
            age_str = '>=' + str(self.age) + ' days old'
        return("%s (%d files/dirs %s)" % (self.name, self.num_files + 1, age_str))


def age(path, max_age=999999):
    """Age of file or dir path in days, truncated at max_age."""
    try:
        age = int((now - os.path.getmtime(path)) / 86400)   # days
    except FileNotFoundError:
        age = max_age
    if (age > max_age):
        age = max_age
    return(age)


def scan_dir(root, max_age=999999):
    """Scan files and dirs under root, returning root node of tree.

    The tree of nodes includes file ages for each directory.
    """
    root_node = None
    last_node = root_node
    for path, dirs, files in os.walk(root, topdown=True):
        num_files = 0
        # path_age is lowest of dir age and age of files contained
        path_age = age(path, max_age)
        for filename in files:
            if (filename in ignore_files):
                continue
            num_files += 1
            filename_age = age(os.path.join(path, filename), max_age)
            if (filename_age<path_age):
                path_age = filename_age
        rel_path = os.path.relpath(path, root)
        node = Node(rel_path, age=path_age, num_files=num_files)
        if (root_node is None):
            node.name = ''  # use '' instead of '.' so common paths work
            root_node = node
        else:
            last_node.add(node)
        last_node = node
        #print("# %s %d" % (rel_path, path_age))
    return(root_node)


def print_tree(root_node, prefix=''):
    """Pre-order print of tree."""
    root_node.preorder(lambda n: print(prefix + str(n)))


def collapse_node(node):
    new_children = []
    for child in node.children:
        if (len(child.children) == 0 and
            child.age >= node.age):
            # combine child into node
            node.num_files += (child.num_files + 1)
        else:
            new_children.append(child)
    node.children = new_children


ignore_files = [ 'Thumbs.db', '.DS_Store' ]
for path in sys.argv[1:]:
    print("Scanning %s" % (path))
    root_node = scan_dir(path, max_age)
    #print_tree(root_node)
    root_node.postorder(collapse_node)
    print("After collapsing less recently updated sub-dirs:\n")
    print_tree(root_node)

