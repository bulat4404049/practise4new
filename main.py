import sys
import lark
from xml.etree.ElementTree import Element, SubElement, tostring

grammar = r"""
start: statement*

statement: const_decl
         | value

const_decl: "const" NAME "=" value

?value: number
      | array
      | dict
      | const_ref

number: SIGNED_FLOAT

array: "array" "(" [value ("," value)*] ")"

dict: "{" [pair ("," pair)*] "}"
pair: NAME ":" value

const_ref: ".[" NAME "]."

NAME: /[A-Za-z]+/
SIGNED_FLOAT: /[+-]?\d+\.\d+/

COMMENT: "#=" /(.|\n)*?/ "=#"

%ignore COMMENT
%ignore /[ \t\r\n]+/
"""

class T(lark.Transformer):
    def start(self, items):
        return items
    def const_decl(self, items):
        return ("const", str(items[0]), items[1])
    def number(self, items):
        return float(items[0])
    def array(self, items):
        return ("array", items)
    def dict(self, items):
        return ("dict", items)
    def pair(self, items):
        return (str(items[0]), items[1])
    def const_ref(self, items):
        return ("ref", str(items[0]))

def eval_all(ast):
    env = {}
    out = []
    def ev(v):
        if isinstance(v, float):
            return v
        if isinstance(v, tuple):
            if v[0] == "array":
                return [ev(x) for x in v[1]]
            if v[0] == "dict":
                return {k: ev(val) for k, val in v[1]}
            if v[0] == "ref":
                return env[v[1]]
        return v
    for node in ast:
        if node[0] == "const":
            val = ev(node[2])
            env[node[1]] = val
            out.append((node[1], val))
        else:
            out.append(ev(node))
    return out

def to_xml(parent, name, value):
    if isinstance(value, float):
        e = SubElement(parent, "number", name=name)
        e.text = str(value)
    elif isinstance(value, list):
        e = SubElement(parent, "array", name=name)
        for v in value:
            to_xml(e, "item", v)
    elif isinstance(value, dict):
        e = SubElement(parent, "dict", name=name)
        for k, v in value.items():
            to_xml(e, k, v)

def main():
    text = sys.stdin.read()
    tree = lark.Lark(grammar, parser="lalr").parse(text)
    ast = T().transform(tree)
    data = eval_all(ast)
    root = Element("config")
    for i, item in enumerate(data):
        if isinstance(item, tuple):
            to_xml(root, item[0], item[1])
        else:
            to_xml(root, f"value{i}", item)
    sys.stdout.write(tostring(root, encoding="unicode"))

if __name__ == "__main__":
    main()
