"""Character adjuster tests."""

from typing import cast
from unittest.mock import AsyncMock, call, patch

import pytest
from discord.ui import Select

from bot import AppCtx, BotchBot
from botchcord.character.adjust import (
    Adjuster,
    BloodAdjuster,
    GroundingAdjuster,
    HealthAdjuster,
    Toggler,
    WillpowerAdjuster,
)
from core.characters import Character, GameLine, Splat
from core.characters.wod import Vampire
from tests.characters import gen_char


@pytest.fixture(autouse=True)
def mock_char_save():
    with patch("core.characters.Character.save") as mocked:
        yield mocked


@pytest.fixture(autouse=True)
def mock_toggler_embed():
    with patch("botchcord.character.adjust.build_embed") as mocked:
        yield mocked


@pytest.fixture(params=[Splat.MORTAL, Splat.VAMPIRE])
def char(request) -> Character:
    return gen_char(GameLine.WOD, request.param, name="Nadea Theron")


@pytest.fixture
def vamp() -> Vampire:
    return gen_char(
        GameLine.WOD,
        Splat.VAMPIRE,
        Vampire,
        generation=13,
        max_bp=10,
        blood_pool=5,
        virtues=[],
    )


@pytest.fixture
def ctx() -> AppCtx:
    bot = BotchBot()
    inter = AsyncMock()
    return AppCtx(bot, inter)


@pytest.fixture
async def toggler(ctx: AppCtx, vamp: Vampire) -> Toggler:
    with patch("bot.AppCtx.edit", new_callable=AsyncMock):
        toggler = Toggler(ctx, vamp)
        return toggler


# These tests have to be async due to Views grabbing the running loop


async def test_init(toggler: Toggler):
    select = cast(Select, toggler.children[0])
    assert select.options[0].default

    names = ("Health", "Willpower", toggler.character.grounding.path)
    for i, name in enumerate(names):
        assert select.options[i].label == f"Adjust: {name}"

    if toggler.character.has_blood_pool:
        assert select.options[-1].label == "Adjust: Blood Pool"

    for i, btn in enumerate(toggler.adjusters[0].buttons):
        assert toggler.children[i + 1] == btn


# "idx" is the button index


@pytest.mark.parametrize(
    "idx,expected",
    [
        (0, "..//XX*"),
        (2, "////XX*"),
        (3, "..///X*"),
        (5, "///XXX*"),
        (6, "..///XX"),
        (8, "///XX**"),
    ],
)
async def test_health_adjuster(idx: int, expected: str, char: Character):
    char.health = ".///XX*"
    toggler = AsyncMock()
    adjuster = HealthAdjuster(toggler, char)

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    await adjuster.callback(inter)
    assert char.health == expected

    toggler.update.assert_called_once_with(inter)


@pytest.mark.parametrize(
    "idx,count,expected",
    [
        (0, 1, "....//"),
        (0, 2, "...../"),
        (0, 3, "......"),
        (0, 4, "......"),
        (2, 1, "..////"),
        (2, 2, "./////"),
        (2, 3, "//////"),
        (2, 4, "//////"),
    ],
)
async def test_willpower_adjuster(
    idx: int,
    count: int,
    expected: str,
    toggler: Toggler,
):
    toggler.character.willpower = "...///"
    adjuster = toggler.adjusters[1]

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)
    assert toggler.character.willpower == expected

    assert toggler.ctx.edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert toggler.character.save.await_count == count


@pytest.mark.parametrize(
    "idx,count,expected",
    [
        (0, 1, 6),
        (0, 2, 5),
        (0, 3, 4),
        (0, 4, 3),
        (0, 5, 2),
        (0, 6, 1),
        (0, 7, 0),
        (0, 8, 0),
        (2, 1, 8),
        (2, 2, 9),
        (2, 3, 10),
        (2, 4, 10),
    ],
)
async def test_grounding_adjuster(idx: int, count: int, expected: int, toggler: Toggler):
    assert toggler.character.grounding.rating == 7

    adjuster = toggler.adjusters[2]

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)
    assert toggler.character.grounding.rating == expected

    assert toggler.ctx.edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert toggler.character.save.await_count == count


@pytest.mark.parametrize(
    "idx,count,expected",
    [
        (0, 1, 4),
        (0, 2, 3),
        (0, 3, 2),
        (0, 4, 1),
        (0, 5, 0),
        (0, 6, 0),
        (2, 1, 6),
        (2, 2, 7),
        (2, 3, 8),
        (2, 4, 9),
        (2, 5, 10),
        (2, 6, 10),
    ],
)
# @patch("botchcord.character.adjust.Toggler._embed")
async def test_blood_pool_adjuster(idx: int, count: int, expected: int, ctx: AppCtx, vamp: Vampire):
    toggler = Toggler(ctx, vamp)
    adjuster = toggler.adjusters[3]
    assert isinstance(adjuster, BloodAdjuster)

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)
    assert vamp.blood_pool == expected

    assert toggler.ctx.edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert toggler.character.save.await_count == count


@pytest.mark.parametrize(
    "cls,track,expected",
    [
        (HealthAdjuster, "....", {0: True, 2: False, 3: True, 5: False, 6: True, 8: False}),
        (HealthAdjuster, "./X*", {0: False, 2: False, 3: False, 5: False, 6: False, 8: False}),
        (HealthAdjuster, "//X*", {0: False, 2: True, 3: False, 5: False, 6: False, 8: False}),
        (HealthAdjuster, "XXX*", {0: True, 2: True, 3: False, 5: True, 6: False, 8: False}),
        (HealthAdjuster, "****", {0: True, 2: True, 3: True, 5: True, 6: False, 8: True}),
        (WillpowerAdjuster, "...", {0: True, 2: False, 3: False}),
        (WillpowerAdjuster, "../", {0: False, 2: False}),
        (WillpowerAdjuster, "///", {0: False, 2: True}),
        (WillpowerAdjuster, ".", {3: True}),
        (WillpowerAdjuster, "..........", {5: True}),
        (GroundingAdjuster, 5, {0: False, 2: False}),
        (GroundingAdjuster, 0, {0: True, 2: False}),
        (GroundingAdjuster, 10, {0: False, 2: True}),
        (BloodAdjuster, 5, {0: False, 2: False}),
        (BloodAdjuster, 0, {0: True, 2: False}),
        (BloodAdjuster, 10, {0: False, 2: True}),
    ],
)
def test_adjuster_button_states(
    vamp: Vampire,
    cls: type[Adjuster],
    track: str | int,
    expected: dict[int, bool],
):
    toggler = AsyncMock()
    if cls is HealthAdjuster:
        vamp.health = cast(str, track)
    elif cls is WillpowerAdjuster:
        vamp.willpower = cast(str, track)
    elif cls is GroundingAdjuster:
        vamp.grounding.rating = cast(int, track)
    elif cls is BloodAdjuster:
        vamp.blood_pool = cast(int, track)
    else:
        raise ValueError(f"Unexpected adjuster: {cls}")
    adjuster = cls(toggler, vamp)

    for idx, state in expected.items():
        assert adjuster.buttons[idx].disabled == state
