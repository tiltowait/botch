"""Specialties input tokenizer."""

from pyparsing import DelimitedList, Group, OneOrMore, ParseException, Word, alphas

import errors

VALID_CHARS = alphas + "_"


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
    trait_group = OneOrMore(
        Group(
            Word(VALID_CHARS).set_results_name("trait")
            + "="
            + DelimitedList(Word(VALID_CHARS), allow_trailing_delim=True).set_results_name(
                "subtraits"
            )
        )
    )

    try:
        matches = []
        for match in trait_group.parse_string(syntax, parse_all=True):
            match = match.as_dict()
            matches.append((match["trait"], match["subtraits"]))
        return matches

    except ParseException as err:
        raise errors.InvalidSyntax(err) from err
