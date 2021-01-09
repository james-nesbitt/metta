"""

Shared utilities

"""

from typing import Dict, List, Any

# @see https://stackoverflow.com/questions/20656135/python-deep-merge-dictionary-data
def _tree_merge(source: Dict[str, Any], destination: Dict[str, Any]):
    """
    Deep merge source into destination

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _tree_merge(value, node)
        else:
            destination[key] = value

    return destination

def _tree_get(node: Dict, key: str):
    """ if key is a "." (dot) delimited path down the Dict as a tree, return the
    matching value, or throw an exception if it isn't found """

    assert key != "", "Must pass a non-empty string key in dot notation"
    assert node, "Empty Dict search is not going to be a good time"

    for step in key.split('.'):
        if step in node:
            node = node[step]
        else:
            # Catch this if you don't like exceptions for incorrect keys
            raise KeyError("Key {} not found in loaded config data. '{}'' was not found".format(key, step))

    return node
