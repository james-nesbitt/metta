"""

Shared tooling and functionality

"""

from typing import Dict, Any

# @see https://stackoverflow.com/questions/20656135/python-deep-merge-dictionary-data
def tree_merge(source: Dict[str, Any], destination: Dict[str, Any]):
    """
    Deep merge source into destination

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """

    assert isinstance(source, dict), "Can't merge a non-dict Source: {}".format(source)
    assert isinstance(destination, dict), "Can't merge a non-dict Destination: {}".format(destination)

    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            tree_merge(value, node)
        else:
            destination[key] = value

    return destination

def tree_get(node: Dict, key: str):
    """ if key is a "." (dot) delimited path down the Dict as a tree, return the
    matching value, or throw a KeyError if it isn't found """

    assert key != "", "Must pass a non-empty string key in dot notation"

    if not node:
        raise ValueError("There was no data in the config so no key match could be made")

    for step in key.split('.'):
        if step in node:
            node = node[step]
        else:
            raise KeyError("Key {} not found in loaded config data. '{}'' was not found".format(key, step))

    return node
