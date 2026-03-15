"""
COMAF-Lite Lexer
Tokenizes COMAF-Lite DSL source into a flat list of tokens.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, line={self.line})"


# Token type constants
TT_KEYWORD   = "KEYWORD"
TT_IDENT     = "IDENT"
TT_NUMBER    = "NUMBER"
TT_STRING    = "STRING"
TT_OP        = "OP"
TT_UNIT      = "UNIT"
TT_BRACE_L   = "BRACE_L"
TT_BRACE_R   = "BRACE_R"
TT_BRACKET_L = "BRACKET_L"
TT_BRACKET_R = "BRACKET_R"
TT_COMMA     = "COMMA"
TT_COLON     = "COLON"
TT_NEWLINE   = "NEWLINE"
TT_INDENT    = "INDENT"
TT_DEDENT    = "DEDENT"
TT_STATE_REF = "STATE_REF"    # |x⟩ literals
TT_COMMENT   = "COMMENT"
TT_EOF       = "EOF"


KEYWORDS = {
    "MODEL", "ENTITY", "CYCLE", "FRAME", "UNITS",
    "STATE", "ENTROPY", "GEOMETRY", "STABILITY", "COLLAPSE",
    "WARP", "EMIT", "TRANSITION", "EVENT",
    "ON", "IF", "AND", "OR", "NOT",
    "evolve", "Schrödinger", "Boltzmann",
    "init", "max", "scale", "hamiltonian",
    "field_equation", "metric",
    "energy", "resolution", "decoherence",
    "velocity", "safety", "target",
    "decay", "collapse", "warp", "emit",
    "Planck", "SI", "Custom",
    "FORCE", "POWER", "PRESSURE", "CURVATURE", "CHARGE",
    "ENTROPY_UNIT", "UNCERTAINTY", "MEASURE",
}

UNITS = {
    "Plameters", "Plaseconds", "Plaminutes", "Plahours", "WarpTicks",
    "WarpTick", "Quasiplancks", "Plajoules", "Plakilograms",
    "RicciBits", "kR", "Sp", "qp", "E_jump",
    "PlaNewtons", "PlaWatts", "PlaPascals",
    "lambda_p", "t_p", "E_p", "m_p",
    "Plasecond", "Plameter", "Plajoule",
}

# Regex patterns (order matters — longest match first)
TOKEN_PATTERNS = [
    (TT_COMMENT,   r'#[^\n]*'),
    (TT_STATE_REF, r'\|[^⟩]+⟩'),               # |x⟩ state literals
    (TT_NUMBER,    r'[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?'),
    (TT_OP,        r'∈|·=|>=|<=|==|!=|\(|\)|[+\-*/^<>=!·\|.½⅓⅔¼¾]'),  # ( ) | . added
    (TT_BRACE_L,   r'\{'),
    (TT_BRACE_R,   r'\}'),
    (TT_BRACKET_L, r'\['),
    (TT_BRACKET_R, r'\]'),
    (TT_COMMA,     r','),
    (TT_COLON,     r':'),
    # Extended IDENT: ASCII + Latin extended + Greek (full block) + math symbols
    # Continuation class includes Latin extended so Schrödinger parses as one token.
    (TT_IDENT,     r'[A-Za-zÀ-ÖØ-öø-ÿ_\u0391-\u03C9∇∈∞ħ⁰¹²³⁴⁵⁶⁷⁸⁹]'
                   r'[A-Za-z0-9À-ÖØ-öø-ÿ_\u0391-\u03C9∇∈∞ħ⁰¹²³⁴⁵⁶⁷⁸⁹\-]*'),
    ('WHITESPACE',  r'[ \t]+'),
    (TT_NEWLINE,   r'\n'),
    ('MISMATCH',   r'.'),
]

_MASTER_RE = re.compile(
    '|'.join(f'(?P<{name.replace("-","_")}>{pat})' for name, pat in TOKEN_PATTERNS),
    re.UNICODE
)


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"Lexer error at line {line}, col {col}: {message}")
        self.line = line
        self.col = col


def tokenize(source: str) -> List[Token]:
    """
    Tokenize COMAF-Lite source into a list of Tokens.
    Strips comments and blank lines from the output.
    """
    tokens: List[Token] = []
    line_num = 1
    line_start = 0

    for mo in _MASTER_RE.finditer(source):
        kind = mo.lastgroup
        value = mo.group()
        col = mo.start() - line_start + 1

        if kind == 'WHITESPACE':
            continue
        elif kind == 'MISMATCH':
            raise LexerError(f"Unexpected character {value!r}", line_num, col)
        elif kind == TT_NEWLINE:
            line_num += 1
            line_start = mo.end()
            tokens.append(Token(TT_NEWLINE, value, line_num - 1, col))
        elif kind == TT_COMMENT:
            # Keep comments as tokens so parser can attach them to AST nodes
            tokens.append(Token(TT_COMMENT, value[1:].strip(), line_num, col))
        elif kind == TT_STATE_REF:
            tokens.append(Token(TT_STATE_REF, value, line_num, col))
        elif kind == TT_NUMBER:
            tokens.append(Token(TT_NUMBER, value, line_num, col))
        elif kind in (TT_BRACE_L, TT_BRACE_R, TT_BRACKET_L, TT_BRACKET_R, TT_COMMA, TT_COLON, TT_OP):
            tokens.append(Token(kind, value, line_num, col))
        elif kind == TT_IDENT:
            if value in KEYWORDS:
                tokens.append(Token(TT_KEYWORD, value, line_num, col))
            elif value in UNITS:
                tokens.append(Token(TT_UNIT, value, line_num, col))
            else:
                tokens.append(Token(TT_IDENT, value, line_num, col))
        else:
            tokens.append(Token(kind, value, line_num, col))

    tokens.append(Token(TT_EOF, "", line_num, 0))
    return tokens


if __name__ == "__main__":
    sample = """
MODEL warp-test:
ENTITY: LocalBubble
CYCLE: CPL-8
FRAME: t ∈ [0, 1 WarpTick]
UNITS: Planck

STATE ψ:
  evolve Schrödinger {
    init: superposition[|0⟩, |1⟩]
    hamiltonian: H_curved(R)
  }
# End of test
"""
    for tok in tokenize(sample):
        if tok.type not in (TT_NEWLINE,):
            print(tok)
