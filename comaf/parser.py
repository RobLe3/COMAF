"""
COMAF-Lite Parser
Converts a token stream into a ProgramNode AST.
"""

import re
from typing import List, Optional, Any

from .lexer import (Token, tokenize, LexerError,
                    TT_KEYWORD, TT_IDENT, TT_NUMBER, TT_STRING,
                    TT_OP, TT_UNIT, TT_BRACE_L, TT_BRACE_R,
                    TT_BRACKET_L, TT_BRACKET_R, TT_COMMA,
                    TT_COLON, TT_NEWLINE, TT_STATE_REF,
                    TT_COMMENT, TT_EOF)
from .ast import (ProgramNode, StateBlockNode, EntropyBlockNode,
                  GeometryBlockNode, StabilityBlockNode, CollapseBlockNode,
                  WarpBlockNode, EmitBlockNode, TransitionBlockNode,
                  AssignmentNode, CommentNode, Node)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"Parse error at line {token.line}: {message} (got {token.type}={token.value!r})")
        self.token = token


class Parser:
    """Recursive descent parser for COMAF-Lite."""

    def __init__(self, tokens: List[Token]):
        # Keep newlines as delimiters; strip only comments
        self.tokens = [t for t in tokens if t.type != TT_COMMENT]
        self.pos = 0

    def skip_newlines(self) -> None:
        """Skip any newline tokens at the current position."""
        while self.pos < len(self.tokens) and self.tokens[self.pos].type == TT_NEWLINE:
            self.pos += 1

    def peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TT_EOF, "", 0, 0)

    def advance(self) -> Token:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, type_: str, value: Optional[str] = None) -> Token:
        tok = self.advance()
        if tok.type != type_:
            raise ParseError(f"Expected {type_!r} but got {tok.type!r}", tok)
        if value is not None and tok.value != value:
            raise ParseError(f"Expected value {value!r}", tok)
        return tok

    def expect_keyword(self, kw: str) -> Token:
        return self.expect(TT_KEYWORD, kw)

    def match(self, type_: str, value: Optional[str] = None) -> bool:
        tok = self.peek()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def consume_if(self, type_: str, value: Optional[str] = None) -> Optional[Token]:
        if self.match(type_, value):
            return self.advance()
        return None

    # ── Collect rest of line as raw expression string ─────────────────────────
    def collect_line_expr(self) -> str:
        """Collect tokens until end-of-line, brace open, or EOF."""
        parts = []
        while self.peek().type not in (TT_EOF, TT_NEWLINE, TT_BRACE_L, TT_BRACE_R):
            parts.append(self.advance().value)
        # consume the newline
        self.consume_if(TT_NEWLINE)
        return " ".join(parts).strip()

    # ── Parse header fields ────────────────────────────────────────────────────
    def parse_header_field(self, keyword: str) -> str:
        self.skip_newlines()
        self.expect_keyword(keyword)
        self.expect(TT_COLON)
        return self.collect_line_expr()

    # ── Main parse entry point ─────────────────────────────────────────────────
    def parse(self) -> ProgramNode:
        self.skip_newlines()
        model_name = None
        if self.match(TT_KEYWORD, "MODEL"):
            self.advance()
            tok = self.advance()
            model_name = tok.value
            self.consume_if(TT_COLON)
            self.skip_newlines()

        entity = self.parse_header_field("ENTITY")
        cycle = self.parse_header_field("CYCLE")
        frame = self.parse_header_field("FRAME")
        units = self.parse_header_field("UNITS")

        blocks: List[Node] = []
        self.skip_newlines()
        while self.peek().type != TT_EOF:
            block = self.parse_block()
            if block is not None:
                blocks.append(block)
            self.skip_newlines()

        return ProgramNode(
            model_name=model_name,
            entity=entity,
            cycle=cycle,
            frame=frame,
            units=units,
            blocks=blocks,
        )

    def parse_block(self) -> Optional[Node]:
        self.skip_newlines()
        tok = self.peek()

        if tok.type == TT_KEYWORD:
            if tok.value == "STATE":
                return self.parse_state_block()
            elif tok.value == "ENTROPY":
                return self.parse_entropy_block()
            elif tok.value == "GEOMETRY":
                return self.parse_geometry_block()
            elif tok.value == "STABILITY":
                return self.parse_stability_block()
            elif tok.value == "IF":
                return self.parse_conditional_block()
            elif tok.value == "ON":
                return self.parse_transition_block()
            else:
                # Skip unknown keywords gracefully
                self.advance()
                return None
        elif tok.type == TT_IDENT:
            # Could be an assignment
            return self.parse_assignment()
        elif tok.type == TT_EOF:
            return None
        else:
            self.advance()  # skip unexpected tokens
            return None

    def parse_state_block(self) -> StateBlockNode:
        self.expect_keyword("STATE")
        name_tok = self.advance()
        name = name_tok.value
        self.expect(TT_COLON)
        self.skip_newlines()
        self.expect_keyword("evolve")
        self.consume_if(TT_KEYWORD, "Schrödinger")
        self.expect(TT_BRACE_L)

        init_val: Any = None
        hamiltonian = ""

        while not self.match(TT_BRACE_R) and self.peek().type != TT_EOF:
            self.skip_newlines()
            if self.match(TT_BRACE_R):
                break
            kw = self.peek()
            if kw.type == TT_KEYWORD and kw.value == "init":
                self.advance()
                self.expect(TT_COLON)
                init_val = self.parse_init_value()
            elif kw.type == TT_KEYWORD and kw.value == "hamiltonian":
                self.advance()
                self.expect(TT_COLON)
                hamiltonian = self.collect_line_expr()
            else:
                self.advance()

        self.consume_if(TT_BRACE_R)
        return StateBlockNode(name=name, init=init_val, hamiltonian=hamiltonian)

    def parse_init_value(self) -> Any:
        """Parse init: value — either a superposition list or a single state."""
        if self.match(TT_KEYWORD, "superposition"):
            self.advance()
            # Collect state refs inside brackets
            states = []
            # skip optional bracket
            while self.peek().type == TT_STATE_REF:
                states.append(self.advance().value)
                self.consume_if(TT_OP, ",")
            if not states:
                # try to collect as raw string
                return self.collect_line_expr()
            return {"superposition": states}
        elif self.peek().type == TT_STATE_REF:
            return self.advance().value
        else:
            return self.collect_line_expr()

    def parse_entropy_block(self) -> EntropyBlockNode:
        self.expect_keyword("ENTROPY")
        name_tok = self.advance()
        name = name_tok.value
        self.expect(TT_COLON)
        self.skip_newlines()
        self.expect_keyword("evolve")
        self.consume_if(TT_KEYWORD, "Boltzmann")
        self.expect(TT_BRACE_L)

        init_val = 0.0
        max_val = 0.0
        scale_val = 0.0
        scale_unit = "Plaseconds"

        while not self.match(TT_BRACE_R) and self.peek().type != TT_EOF:
            self.skip_newlines()
            if self.match(TT_BRACE_R):
                break
            kw = self.peek()
            if kw.type == TT_KEYWORD and kw.value == "init":
                self.advance(); self.expect(TT_COLON)
                init_val = float(self.advance().value)
            elif kw.type == TT_KEYWORD and kw.value in ("max",):
                self.advance(); self.expect(TT_COLON)
                max_val = float(self.advance().value)
            elif kw.type == TT_KEYWORD and kw.value == "scale":
                self.advance(); self.expect(TT_COLON)
                scale_val = float(self.advance().value)
                if self.peek().type == TT_UNIT:
                    scale_unit = self.advance().value
            else:
                self.advance()

        self.consume_if(TT_BRACE_R)
        return EntropyBlockNode(
            name=name, init=init_val, max_val=max_val,
            scale=scale_val, scale_unit=scale_unit
        )

    def parse_geometry_block(self) -> GeometryBlockNode:
        self.expect_keyword("GEOMETRY")
        self.expect(TT_COLON)
        field_eq = ""

        # Check for field_equation keyword
        if self.match(TT_KEYWORD, "field_equation"):
            self.advance()
            self.expect(TT_COLON)
            field_eq = self.collect_line_expr()

        return GeometryBlockNode(field_equation=field_eq)

    def parse_stability_block(self) -> StabilityBlockNode:
        self.expect_keyword("STABILITY")
        self.expect(TT_COLON)
        self.expect_keyword("metric")
        metric_name = self.advance().value
        self.consume_if(TT_OP, "=")
        expression = self.collect_line_expr()
        return StabilityBlockNode(metric_name=metric_name, expression=expression)

    def parse_conditional_block(self):
        """Parse IF condition: collapse|warp|emit { ... }"""
        self.expect_keyword("IF")
        condition_parts = []
        # Collect condition until colon
        while not self.match(TT_COLON) and self.peek().type != TT_EOF:
            condition_parts.append(self.advance().value)
        condition = " ".join(condition_parts)
        self.expect(TT_COLON)

        # Determine block type
        action_tok = self.peek()
        action = action_tok.value if action_tok.type == TT_KEYWORD else ""

        if action == "collapse":
            self.advance()
            self.expect(TT_BRACE_L)
            body = self._parse_body_kv()
            self.consume_if(TT_BRACE_R)
            return CollapseBlockNode(
                condition=condition,
                energy=body.get("energy"),
                resolution=body.get("resolution"),
                decoherence=body.get("decoherence"),
            )
        elif action == "warp":
            self.advance()
            self.expect(TT_BRACE_L)
            body = self._parse_body_kv()
            self.consume_if(TT_BRACE_R)
            return WarpBlockNode(
                condition=condition,
                velocity=body.get("velocity"),
                safety=body.get("safety"),
                target=body.get("target"),
            )
        elif action == "emit":
            self.advance()
            self.expect(TT_BRACE_L)
            body = self._parse_body_kv()
            self.consume_if(TT_BRACE_R)
            return EmitBlockNode(
                condition=condition,
                energy=body.get("energy"),
                decay=body.get("decay"),
            )
        else:
            # Unknown action — skip
            return None

    def _parse_body_kv(self) -> dict:
        """Parse key: value pairs inside a block until }."""
        result = {}
        while not self.match(TT_BRACE_R) and self.peek().type != TT_EOF:
            self.skip_newlines()
            if self.match(TT_BRACE_R):
                break
            key_tok = self.advance()
            if key_tok.type == TT_NEWLINE:
                continue
            if self.match(TT_COLON):
                self.advance()
                value = self.collect_line_expr()
                result[key_tok.value] = value
        return result

    def parse_transition_block(self) -> TransitionBlockNode:
        self.expect_keyword("ON")
        event_parts = []
        while not self.match(TT_COLON) and self.peek().type != TT_EOF:
            event_parts.append(self.advance().value)
        event_name = ".".join(event_parts)
        self.expect(TT_COLON)
        statements = []
        # Collect remaining as statement strings
        while self.peek().type not in (TT_EOF,) and not self.match(TT_KEYWORD):
            stmt_parts = []
            while self.peek().type not in (TT_EOF,) and not (
                self.match(TT_KEYWORD, "ON") or self.match(TT_KEYWORD, "IF") or
                self.match(TT_KEYWORD, "STATE") or self.match(TT_KEYWORD, "ENTROPY")
            ):
                if self.peek().type == TT_BRACE_L:
                    break
                stmt_parts.append(self.advance().value)
                if not stmt_parts:
                    break
            if stmt_parts:
                statements.append(" ".join(stmt_parts))
            break
        return TransitionBlockNode(event_name=event_name, statements=statements)

    def parse_assignment(self) -> AssignmentNode:
        target = self.advance().value
        op_tok = self.advance()
        expr = self.collect_line_expr()
        return AssignmentNode(target=target, operator=op_tok.value, expression=expr)


def parse(source: str) -> ProgramNode:
    """Parse COMAF-Lite source text into a ProgramNode AST."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse()
