from mcnpy.errors import *
from mcnpy.input_parser.parser_base import MCNP_Parser, MetaBuilder
from mcnpy.input_parser import syntax_node


class DataParser(MCNP_Parser):
    """
    A parser for almost all data inputs.

    :returns: a syntax tree for the data input.
    :rtype: SyntaxNode
    """

    debugfile = None

    @_(
        "introduction data",
        "introduction data parameters",
    )
    def data_input(self, p):
        ret = {}
        for key, node in p.introduction.nodes.items():
            ret[key] = node
        ret["data"] = p.data
        if hasattr(p, "parameters"):
            ret["parameters"] = p.parameters
        return syntax_node.SyntaxNode("data", ret)

    @_("TEXT", "PARTICLE")
    def classifier(self, p):
        classifier = syntax_node.ClassifierNode()
        if hasattr(p, "TEXT"):
            text = p.TEXT
        else:
            text = p.PARTICLE
        classifier.prefix = syntax_node.ValueNode(text, str)
        return classifier

    @_(
        "classifier_phrase",
        "classifier_phrase KEYWORD padding",
        "padding classifier_phrase",
        "padding classifier_phrase KEYWORD padding",
    )
    def introduction(self, p):
        ret = {}
        if isinstance(p[0], syntax_node.PaddingNode):
            ret["start_pad"] = p[0]
        else:
            ret["start_pad"] = syntax_node.PaddingNode()
        ret["classifier"] = p.classifier_phrase
        if hasattr(p, "KEYWORD"):
            ret["keyword"] = syntax_node.ValueNode(p.KEYWORD, str, padding=p[-1])
        else:
            ret["keyword"] = syntax_node.ValueNode(None, str, padding=None)
        return syntax_node.SyntaxNode("data intro", ret)

    @_("number_sequence", "isotope_fractions")
    def data(self, p):
        return p[0]

    @_("zaid_phrase number_phrase")
    def isotope_fraction(self, p):
        return p

    @_("isotope_fraction", "isotope_fractions isotope_fraction")
    def isotope_fractions(self, p):
        if hasattr(p, "isotope_fractions"):
            fractions = p.isotope_fractions
        else:
            fractions = syntax_node.IsotopesNode("isotope list")
        fractions.append(p.isotope_fraction)
        return fractions

    @_("ZAID", "ZAID padding")
    def zaid_phrase(self, p):
        return self._flush_phrase(p, str)

    # TODO test this style of parameter
    # for material libraries
    @_("classifier param_seperator NUMBER text_phrase")
    def parameter(self, p):
        return syntax_node.SyntaxNode(
            p.classifier.prefix.value,
            {
                "classifier": p.classifier,
                "seperator": p.param_seperator,
                "data": syntax_node.ValueNode(p.NUMBER + p.text_phrase, str),
            },
        )


class ClassifierParser(DataParser):
    """
    A parser for parsing the first word or classifier of a data input.

    :returns: the classifier of the data input.
    :rtype: ClassifierNode
    """

    debugfile = None

    @_("classifier")
    def data_classifier(self, p):
        return syntax_node.SyntaxNode(
            "data input classifier", {"classifier": p.classifier}
        )
