
from .. import tools

def test_tree_merge():
    """" test the tools._tree_merge() function """

    one = {
        "1": "one from one"
    }
    two = {
        "1": "one from two",
        "2": "two from two"
    }

    merged = tools._tree_merge(two, one)
    """ one and two merged with two being a higher priority """

    assert merged["1"] == two["1"]
