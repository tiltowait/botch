"""Functions for adding/updating character traits. Not inclusive of subtraits."""


from pyparsing import (
    Dict,
    Group,
    OneOrMore,
    ParseException,
    Suppress,
    Word,
    alphas,
    nums,
)


def parse_input(user_input: str):
    """Parse the user's input and find all the traits and ratings."""
    alphascore = alphas + "_"
    equals = Suppress("=")
    trait = Group(Word(alphas, alphascore + nums) + equals + Word(nums))
    traits = Dict(OneOrMore(trait))

    try:
        parsed = traits.parse_string(user_input, parse_all=True)
    except ParseException:
        raise SyntaxError("Invalid syntax! **Example:** `Brawl=3 Strength=2`")

    # Create dictionary, converting ratings to ints
    traits_dict = {}
    seen = set()
    for trait, rating in parsed:
        if trait in seen:
            raise SyntaxError(f"Duplicate trait: {trait}")

        seen.add(trait)
        traits_dict[trait] = int(rating)

    return traits_dict
