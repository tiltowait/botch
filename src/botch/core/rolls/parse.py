"""Roll-parsing utilities."""

import ast
import re
from typing import cast

from pyparsing import Combine, Opt, ParseException, Word, ZeroOrMore, nums, one_of

from botch import errors
from botch.core.characters import Character
from botch.core.utils.parsing import TRAIT


class RollParser:
    def __init__(self, syntax: str, character: Character | None):
        self.raw_syntax = syntax
        self.character = character
        self.pool: list[str | int] = []
        self.equation: list[str | int] = []
        self.num_dice = 0
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
        for elem in self.tokenize():
            if elem in {"+", "-"} or isinstance(elem, int):
                self.pool.append(elem)
                self.equation.append(elem)
            elif elem.upper() == "WP":
                self.pool.append("WP")
                self.equation.append(0)
            else:
                self._process_trait_token(elem, use_key)

        self.num_dice = evaluate("".join(map(str, self.equation)))

        return self

    def _process_trait_token(self, trait_name: str, use_key: bool):
        """Process a trait token and update roll components.

        The matched trait name (or key) is added to the pool, the rating is
        added to the equation, and any specialties are added to the specialties
        list.

        Args:
            trait_name: The name of the trait to find. May be truncated.
            use_key: Whether to use "Trait.Subtrait" or "Trait (Subtrait)".

        Raises:
            RollError if no character is set.
            TraitNotFound if no matches are found.
            AmbiguousTraitError if multiple matches are found.
        """
        if self.character is None:
            raise errors.RollError(f"You need a character to roll `{self.raw_syntax}`.")

        traits = self.character.match_traits(trait_name)
        match len(traits):
            case 1:
                trait = traits[0]
                if use_key:
                    self.pool.append(trait.key)
                else:
                    self.pool.append(trait.name)
                self.equation.append(trait.rating)

                if trait.subtraits:
                    self.specialties.extend(trait.subtraits)
            case 0:
                raise errors.TraitNotFound(self.character, trait_name)
            case _:
                raise errors.AmbiguousTraitError(trait_name, [t.key for t in traits])

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


def evaluate(expr: str) -> int:
    """Safely evaluate a mathematical expression (+/- only)."""

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
