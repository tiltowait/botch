"""Roll-parsing utilities."""

import ast
import operator as op
import re

from pyparsing import (
    Combine,
    Opt,
    ParseException,
    Word,
    ZeroOrMore,
    alphas,
    nums,
    one_of,
)

import errors
from botch.characters import Character


class RollParser:
    def __init__(self, syntax: str, character: Character | None):
        self.raw_syntax: str = syntax
        self.character: Character = character
        self.pool: list[str] = []
        self.equation: list[str | int] = []
        self.dice = 0
        self.specialties = None

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
            trait = Combine(Opt(Word(alphas)) + ZeroOrMore("." + Opt(Word(alphas))))
            operand = Word(nums) | trait
            eq = operand + ZeroOrMore(one_of("+ -") + operand)
            parsed = eq.parse_string(self.raw_syntax, parse_all=True).as_list()

            # Convert to list[str | int]
            for i, elem in enumerate(parsed):
                try:
                    parsed[i] = int(elem)
                except ValueError:
                    pass

            return parsed

        except ParseException as err:
            raise errors.InvalidSyntax(err) from err

    def parse(self):
        """Parse the roll, populating pool, equation, and dice."""
        if self.needs_character and self.character is None:
            raise errors.RollError(f"You need a character to roll `{self.raw_syntax}`.")

        specialties = []
        for elem in self.tokenize():
            if elem in {"+", "-"} or isinstance(elem, int):
                self.pool.append(elem)
                self.equation.append(elem)
            elif elem.upper() == "WP":
                self.pool.append("WP")
                self.equation.append(0)
            else:
                traits = self.character.match_traits(elem)
                if not traits:
                    raise errors.TraitNotFound(self.character, elem)
                elif len(traits) > 1:
                    raise errors.AmbiguousTraitError(elem, [t.key for t in traits])

                # Single trait found!
                match = traits[0]
                self.pool.append(match.name)
                self.equation.append(match.rating)

                if match.subtraits:
                    specialties.extend(match.subtraits)

        self.dice = eval_expr("".join(map(str, self.equation)))
        if specialties:
            self.specialties = specialties

        return self


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
