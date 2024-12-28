"""Roll-parsing utilities."""

import ast
import re
from typing import cast

from pyparsing import Combine, Opt, ParseException, Word, ZeroOrMore, nums, one_of

import errors
from core.characters import Character
from core.utils.parsing import TRAIT


class RollParser:
    def __init__(self, syntax: str, character: Character | None):
        self.raw_syntax = syntax
        self.character = character
        self.pool: list[str | int] = []
        self.equation: list[str | int] = []
        self.num_dice: int = 0
        self.specialties: list[str] = []

    @property
    def using_wp(self) -> bool:
        """Whether the roll uses Willpower."""
        return "WP" in self.pool

    @property
    def needs_character(self) -> bool:
        """Whether the roll syntax requires a character."""
        # WP isn't a trait, so we have to filter that out
        operands = re.split(r"[\s+-]", self.raw_syntax.upper())
        pool_without_wp = "".join(filter(lambda s: s != "WP", map(str, operands)))

        return re.search(r"[A-Za-z_.]", pool_without_wp) is not None

    @property
    def specialty_used(self) -> bool:
        """Whether the user specified a specialty."""
        return "." in self.raw_syntax

    def tokenize(self) -> list[str | int]:
        """Validate the syntax and return the tokenized list."""
        try:
            trait = Combine(Opt(TRAIT) + ZeroOrMore("." + Opt(TRAIT)))
            operand = Word(nums) | trait

            expr = operand + ZeroOrMore(one_of("+ -") + operand)

            return [
                int(token) if token.isdigit() else token
                for token in expr.parse_string(self.raw_syntax, parse_all=True)
            ]

        except ParseException as err:
            raise errors.InvalidSyntax(f"Invalid syntax at column {err.loc}") from err

    def parse(self, use_key=False):
        """Parse the roll, populating pool, equation, and dice."""
        if self.needs_character and self.character is None:
            raise errors.RollError(f"You need a character to roll `{self.raw_syntax}`.")

        for elem in self.tokenize():
            if elem in {"+", "-"} or isinstance(elem, int):
                self.pool.append(elem)
                self.equation.append(elem)
            elif elem.upper() == "WP":
                self.pool.append("WP")
                self.equation.append(0)
            else:
                assert self.character is not None
                traits = self.character.match_traits(elem)
                if not traits:
                    raise errors.TraitNotFound(self.character, elem)
                elif len(traits) > 1:
                    raise errors.AmbiguousTraitError(elem, [t.key for t in traits])

                # Single trait found!
                match = traits[0]
                if use_key:
                    self.pool.append(match.key)
                else:
                    self.pool.append(match.name)
                self.equation.append(match.rating)

                if match.subtraits:
                    self.specialties.extend(match.subtraits)

        self.num_dice = evaluate("".join(map(str, self.equation)))

        return self

    @classmethod
    def can_roll(cls, char: Character, syntax: str) -> bool:
        """Returns true if the character can make the roll."""
        try:
            rp = cls(syntax, char)
            rp.parse()
        except errors.TraitNotFound:
            return False
        except errors.AmbiguousTraitError:
            return True
        else:
            return True


# Math Helpers

# We could use pandas for this, but this is built-in and considerably faster,
# which makes a difference when calculating probabilities.


def evaluate(expr: str) -> int:
    """Evaluate a mathematical expression with +/-."""

    def _eval(node: ast.AST) -> int:
        """Recursively evaluate the operands and operations."""
        match node:
            case ast.Constant():
                # Technically, this could also be a float or complex, but we
                # know that it will only ever be an int.
                return cast(int, node.n)
            case ast.BinOp(left=left, op=op, right=right):
                match op:
                    case ast.Add():
                        return _eval(left) + _eval(right)
                    case ast.Sub():
                        return _eval(left) - _eval(right)
                    case _:
                        raise TypeError(f"Unsupported operator: {op}")
            case ast.UnaryOp(op=op, operand=operand):
                match op:
                    case ast.UAdd():
                        return _eval(operand)
                    case ast.USub():
                        return -_eval(operand)
                    case _:
                        raise TypeError(f"Unsupported operator: {op}")
            case _:
                raise TypeError(f"Unsupported node type: {node}")

    return _eval(ast.parse(expr, mode="eval").body)
