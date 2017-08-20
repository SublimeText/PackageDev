from collections import OrderedDict

from yaml.loader import Reader, Scanner, Parser, Composer, SafeConstructor, Resolver
from yaml.nodes import SequenceNode, MappingNode
from yaml.constructor import ConstructorError


class SafeOrderedDictConstructor(SafeConstructor):

    def construct_yaml_omap(self, node):
        # The functionality is already available
        # but it's just returned as a list of tuples
        # instead of being put into an OrderedDict,
        # so we do everything ourselves.
        omap = OrderedDict()
        yield omap
        if not isinstance(node, SequenceNode):
            raise ConstructorError("while constructing an ordered map",
                                   node.start_mark,
                                   "expected a sequence, but found %s" % node.id,
                                   node.start_mark)
        for subnode in node.value:
            if not isinstance(subnode, MappingNode):
                raise ConstructorError("while constructing an ordered map",
                                       node.start_mark,
                                       "expected a mapping of length 1, but found %s" % subnode.id,
                                       subnode.start_mark)
            if len(subnode.value) != 1:
                raise ConstructorError("while constructing an ordered map",
                                       node.start_mark,
                                       "expected a single mapping item, but found %d items"
                                       % len(subnode.value),
                                       subnode.start_mark)
            key_node, value_node = subnode.value[0]
            key = self.construct_object(key_node)
            value = self.construct_object(value_node)
            omap[key] = value


SafeOrderedDictConstructor.add_constructor(
    'tag:yaml.org,2002:omap',
    SafeOrderedDictConstructor.construct_yaml_omap
)


class SaveOmapLoader(Reader, Scanner, Parser, Composer, SafeOrderedDictConstructor, Resolver):

    def __init__(self, stream):
        # idk why yaml isn't using super internally here, but we just copy the code
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeOrderedDictConstructor.__init__(self)
        Resolver.__init__(self)
