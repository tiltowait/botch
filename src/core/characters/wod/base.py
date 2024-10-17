"""Base WoD character attributes."""

from core.characters.base import Character, Trait


class WoD(Character):
    """Abstract class for WoD characters. Used primarily for inheritance tree
    to let Beanie know what class to instantiate."""

    @staticmethod
    def _trait_sort_key(t: Trait) -> str:
        """The key used for insorting traits."""
        Cat = Trait.Category
        Sub = Trait.Subcategory

        params = {
            Cat.ATTRIBUTE: "a",
            Cat.ABILITY: "b",
            Sub.PHYSICAL: "a",
            Sub.MENTAL: "b",
            Sub.SOCIAL: "c",
            Sub.TALENTS: "a",
            Sub.SKILLS: "b",
            Sub.KNOWLEDGES: "c",
            # Preserve character sheet attribute order
            "Strength": "0",
            "Dexterity": "1",
            "Stamina": "2",
            "Charisma": "3",
            "Manipulation": "4",
            "Appearance": "5",
            "Perception": "6",
            "Intelligence": "7",
            "Wits": "8",
        }

        # Example: Brawl is an ability -> physical. Key: b.a.brawl
        primary = params.get(t.category, "zzz")
        secondary = params.get(t.subcategory, "zzz")
        tertiary = params.get(t.name, t.name)
        return f"{primary}.{secondary}.{tertiary}".casefold()
