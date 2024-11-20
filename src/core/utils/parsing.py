"""Shared "trait" pyparsing object."""

from pyparsing import White, Word, ZeroOrMore, alphas

__alphascore = alphas + "_"
TRAIT = Word(__alphascore) + ZeroOrMore(White().set_parse_action(lambda: " ") + Word(__alphascore))
