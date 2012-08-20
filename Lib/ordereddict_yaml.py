# Defines (Safe)Loaders and a SafeDumper for YAML supporting ordered
# dictionaries. Also adds a representer to the default Dumper.

import yaml

from yaml.loader      import SafeLoader, Loader
from yaml.dumper      import SafeDumper
from yaml.constructor import *

try:
    # included in standard lib from Python 2.7
    # note: Sublime Text uses 2.6
    from collections import OrderedDict
except ImportError:
    # try importing the backported drop-in replacement
    # it's available on PyPI
    from ordereddict import OrderedDict


__all__ = ['OrderedDictLoader', 'OrderedDictSafeLoader', 'OrderedDictSafeDumper']


class BaseOrderedDictLoader(object):
    # http://stackoverflow.com/questions/5121931

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise ConstructorError(None, None, 'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = OrderedDict()

        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise ConstructorError('while constructing a mapping', node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value

        return mapping


class OrderedDictLoader(Loader):
    """A YAML loader that loads mappings into ordered dictionaries.
    """
    pass

OrderedDictLoader.add_constructor(u'tag:yaml.org,2002:map',
        OrderedDictLoader.construct_yaml_map)
OrderedDictLoader.add_constructor(u'tag:yaml.org,2002:omap',
        OrderedDictLoader.construct_yaml_map)


class OrderedDictSafeLoader(SafeLoader):
    """A YAML (safe) loader that loads mappings into ordered dictionaries.
    """
    pass


OrderedDictSafeLoader.add_constructor(u'tag:yaml.org,2002:map',
        OrderedDictLoader.construct_yaml_map)
OrderedDictSafeLoader.add_constructor(u'tag:yaml.org,2002:omap',
        OrderedDictLoader.construct_yaml_map)


class OrderedDictSafeDumper(SafeDumper):
    """A YAML (safe) dumper that dumps OrderedDicts according to
    their order.
    """

    def represent_ordereddict(self, data):
        # Bypass the sorting in represent_mapping
        return self.represent_mapping(u'tag:yaml.org,2002:map', data.items())

OrderedDictSafeDumper.add_representer(OrderedDict,
        OrderedDictSafeDumper.represent_ordereddict)
# add to the default dumper
yaml.add_representer(OrderedDict,
        OrderedDictSafeDumper.represent_ordereddict)
