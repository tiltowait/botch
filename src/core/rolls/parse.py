"""Roll-parsing utilities."""

import ast
import operator as op
import re

from pyparsing import (
    Combine,
    Opt,
    ParseException,
    White,
    Word,
    ZeroOrMore,
    alphas,
    nums,
    one_of,
)

import errors
from core.characters import Character


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
            alphascore = alphas + "_"
            # Allow words with spaces, but combine them
            word_part = Word(alphascore) + ZeroOrMore(
                White().set_parse_action(lambda: " ") + Word(alphascore)
            )
            trait = Combine(Opt(word_part) + ZeroOrMore("." + Opt(word_part)))
            operand = Word(nums) | trait

            expr = operand + ZeroOrMore(one_of("+ -") + operand)

            return [
                int(token) if token.isdigit() else token
                for token in expr.parseString(self.raw_syntax, parseAll=True)
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

        self.num_dice = eval_expr("".join(map(str, self.equation)))

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

OPERATORS = {ast.Add: op.add, ast.Sub: op.sub, ast.UAdd: op.pos, ast.USub: op.neg}


def eval_expr(expr):
    """Evaluate a mathematical string expression. Safer than using eval."""
    return eval_(ast.parse(expr, mode="eval").body)


def eval_(node):
    """Recursively evaluate a mathematical expression. Only handles +/-."""
    if isinstance(node, ast.Num):
        return node.n

    if isinstance(node, ast.BinOp):
        return OPERATORS[type(node.op)](eval_(node.left), eval_(node.right))

    if isinstance(node, ast.UnaryOp):
        return OPERATORS[type(node.op)](eval_(node.operand))

    raise TypeError(node)
