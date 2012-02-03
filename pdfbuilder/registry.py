_layout_templates = {}
def register_template(func, id, name=None):
    _layout_templates[id] = (func, name or id)
def available_templates():
    return [(key, val[1]) for key, val in _layout_templates.items()]
def get_template(id):
    return _layout_templates[id][0]

_orderings = {}
def register_ordering(tuple, id, name=None):
    _orderings[id] = (tuple, name or id)
def available_orderings():
    return [(key, val[1]) for key, val in _orderings.items()]
def get_ordering(id):
    return _orderings[id][0]
register_ordering(None, "none", "Do not order entries")

_groupings = {}
def register_grouping(grouping_fn, id, name=None):
    _groupings[id] = (grouping_fn, name or id)
def available_groupings():
    return [(key, val[1]) for key, val in _groupings.items()]
def get_grouping(id):
    return _groupings[id][0]

def default_bucket_selector(buckets, entry):
    """
    Given a dict of lists, return the key of the list to put 
    the given entry into, creating the proper list in the dict if necessary.

    This implementation puts all entries into the same bucket.
    """
    if 'default' not in buckets:
        buckets['default'] = []
    return 'default'
register_grouping(default_bucket_selector, "none",
                  "Do not group entries (single PDF)")
