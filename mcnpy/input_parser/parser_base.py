from mcnpy.input_parser.tokens import MCNP_Lexer
from mcnpy.input_parser import semantic_node
from sly import Parser
import sly

_dec = sly.yacc._decorator


class MetaBuilder(sly.yacc.ParserMeta):
    protected_names = {
        "debugfile",
        "errok",
        "error",
        "index_position",
        "line_position",
        "log",
        "parse",
        "restart",
        "tokens",
    }

    def __new__(meta, classname, bases, attributes):
        if classname != "MCNP_Parser":
            for attr_name in dir(MCNP_Parser):
                if (
                    not attr_name.startswith("_")
                    and attr_name not in MetaBuilder.protected_names
                ):
                    func = getattr(MCNP_Parser, attr_name)
                    attributes[attr_name] = func
        cls = super().__new__(meta, classname, bases, attributes)
        return cls


class MCNP_Parser(Parser, metaclass=MetaBuilder):
    tokens = MCNP_Lexer.tokens

    @_("NUMBER", "NUMBER padding")
    def number_phrase(self, p):
        if len(p) > 1:
            padding = p[1]
        else:
            padding = None
        return semantic_node.ValueNode(p[0], padding)

    @_("number_phrase", "number_sequence number_phrase")
    def number_sequence(self, p):
        return p

    @_("NULL", "NULL padding")
    def null_phrase(self, p):
        return p

    @_("TEXT", "TEXT padding")
    def text_phrase(self, p):
        if len(p) > 1:
            padding = p[1]
        else:
            padding = None
        return semantic_node.ValueNode(p[0], padding)

    @_("SPACE")
    def padding(self, p):
        return semantic_node.PaddingNode(p.SPACE)

    @_("padding SPACE", "padding DOLLAR_COMMENT", "padding COMMENT", 'padding "&"')
    def padding(self, p):
        p[0].append(p[1])
        return p[0]

    @_('"="', "SPACE")
    def param_seperator(self, p):
        return p

    @_(
        "KEYWORD param_seperator number_sequence",
        "KEYWORD param_seperator text_phrase",
    )
    def parameter(self, p):
        return p

    @_("parameter", "parameters parameter")
    def parameters(self, p):
        if len(p) == 1:
            params = semantic_node.ParametersNode()
            param = p[0]
        else:
            params = p[0]
            param = p[1]
        params.append(*param[1:])
        return params
