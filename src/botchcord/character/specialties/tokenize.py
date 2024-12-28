"""Specialties input tokenizer."""

from pyparsing import DelimitedList, Group, ParseException

import errors
from core.utils.parsing import TRAIT


def tokenize(syntax: str) -> list[tuple[str, list[str]]]:
    """
    Tokenize subtrait syntax.

    Args:
        syntax (str): The input string to tokenize.

    Returns:
        list[tuple[str, list[str]]]: A list of tuples, each containing a trait and its subtraits.

    Raises:
        errors.InvalidSyntax: If the input syntax is invalid.
    """
    trait_group = DelimitedList(
        Group(
            TRAIT.set_results_name("trait")
            + "="
            + DelimitedList(TRAIT, allow_trailing_delim=True).set_results_name(
                "subtraits"
            )
        ),
        delim=";",
        allow_trailing_delim=True,
    )

    try:
        matches = trait_group.parse_string(syntax, parse_all=True)
        return [(match.trait, match.subtraits.as_list()) for match in matches]

    except ParseException as err:
        raise errors.InvalidSyntax(err) from err
