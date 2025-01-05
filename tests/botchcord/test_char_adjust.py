"""Character adjuster tests."""

from typing import cast
from unittest.mock import ANY, AsyncMock, Mock, call, patch

import discord
import pytest
from discord.ui import Select

from bot import AppCtx, BotchBot
from botchcord.character.adjust import (
    Adjuster,
    GroundingAdjuster,
    HealthAdjuster,
    MummyPillarAdjuster,
    MummySekhemAdjuster,
    Toggler,
    VampAdjuster,
    WillpowerAdjuster,
    adjust,
)
from core.characters import Character, GameLine, Splat, cofd, wod
from tests.characters import gen_char
from utils import max_vtm_bp, max_vtr_vitae

VampireType = wod.Vampire | cofd.Vampire


@pytest.fixture(autouse=True)
def mock_use_emojis():
    with patch("botchcord.settings.use_emojis", new_callable=AsyncMock) as mocked:
        mocked.return_value = False
        yield mocked


@pytest.fixture(params=[Splat.MORTAL, Splat.VAMPIRE])
def char(request) -> Character:
    return gen_char(GameLine.WOD, request.param, name="Nadea Theron")


@pytest.fixture
def vamp() -> wod.Vampire:
    return gen_char(
        GameLine.WOD,
        Splat.VAMPIRE,
        wod.Vampire,
        generation=13,
        max_bp=10,
        blood_pool=5,
        virtues=[],
    )


@pytest.fixture
def cvamp() -> cofd.Vampire:
    return gen_char(
        GameLine.COFD,
        Splat.VAMPIRE,
        cofd.Vampire,
        blood_potency=2,
        max_vitae=10,
        vitae=5,
    )


@pytest.fixture
def mummy() -> cofd.Mummy:
    mummy = gen_char(
        GameLine.COFD,
        Splat.MUMMY,
        cofd.Mummy,
        sekhem=8,
    )

    for pillar in mummy.pillars:
        pillar.rating = 3
        pillar.temporary = 3

    return mummy


@pytest.fixture(params=["vamp", "cvamp"])
def avamp(request: pytest.FixtureRequest) -> VampireType:
    return request.getfixturevalue(request.param)


@pytest.fixture
def ctx() -> AppCtx:
    bot = BotchBot()
    inter = AsyncMock()
    return AppCtx(bot, inter)


@pytest.fixture
async def toggler(ctx: AppCtx, vamp: wod.Vampire) -> Toggler:
    with patch("bot.AppCtx.edit", new_callable=AsyncMock):
        toggler = Toggler(ctx, vamp)
        return toggler


@pytest.fixture
async def mummy_toggler(ctx: AppCtx, mummy: cofd.Mummy) -> Toggler:
    with patch("bot.AppCtx.edit", new_callable=AsyncMock):
        toggler = Toggler(ctx, mummy)
        return toggler


# These tests have to be async due to Views grabbing the running loop


async def test_init(toggler: Toggler):
    select = cast(Select, toggler.children[0])
    assert select.options[0].default

    names = ("Health", "Willpower", toggler.character.grounding.path)
    for i, name in enumerate(names):
        assert select.options[i].label == f"Adjust: {name}"

    if toggler.character.has_blood_pool:
        assert select.options[-1].label == "Adjust: Vampirism"

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
        (3, 1, "..///"),
        (3, 10, "/"),
        (5, 1, "....///"),
        (5, 10, ".......///"),
    ],
)
async def test_willpower_adjuster(
    mock_edit: AsyncMock,
    mock_char_save: AsyncMock,
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

    assert mock_edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert mock_char_save.await_count == count


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
async def test_grounding_adjuster(
    mock_edit: AsyncMock,
    mock_char_save: AsyncMock,
    idx: int,
    count: int,
    expected: int,
    toggler: Toggler,
):
    assert toggler.character.grounding.rating == 7

    adjuster = toggler.adjusters[2]

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)
    assert toggler.character.grounding.rating == expected

    assert mock_edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert mock_char_save.await_count == count


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
        (3, 1, (9, 5)),
        (3, 6, (4, 4)),
        (3, 10, (1, 1)),
        (5, 1, (11, 5)),
        (5, 100, (50, 5)),
        (6, 1, (12, max_vtm_bp(12))),
        (6, 6, (7, max_vtm_bp(7))),
        (6, 40, (3, max_vtm_bp(3))),
        (8, 1, (14, max_vtm_bp(14))),
        (8, 10, (15, max_vtm_bp(15))),
    ],
)
async def test_wod_vamp_adjuster(
    mock_edit: AsyncMock,
    mock_char_save: AsyncMock,
    idx: int,
    count: int,
    expected: int | tuple[int, ...],
    ctx: AppCtx,
    vamp: wod.Vampire,
):
    toggler = Toggler(ctx, vamp)
    adjuster = toggler.adjusters[3]
    assert isinstance(adjuster, VampAdjuster)

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)

    match idx:
        case 0 | 2:
            assert vamp.blood_pool == expected
        case 3 | 5:
            assert isinstance(expected, tuple)
            mbp, bp = expected
            assert vamp.max_bp == mbp
            assert vamp.blood_pool == bp
        case 6 | 8:
            assert isinstance(expected, tuple)
            gen, mbp = expected
            assert vamp.generation == gen
            assert vamp.max_bp == mbp

    assert mock_edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert mock_char_save.await_count == count


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
        (3, 1, (9, 5)),
        (3, 6, (4, 4)),
        (3, 10, (1, 1)),
        (5, 1, (11, 5)),
        (5, 100, (50, 5)),
        (6, 1, (1, max_vtr_vitae(1))),
        (6, 6, (0, max_vtr_vitae(0))),
        (8, 1, (3, max_vtr_vitae(3))),
        (8, 10, (10, max_vtr_vitae(10))),
    ],
)
async def test_cofd_vamp_adjuster(
    mock_edit: AsyncMock,
    mock_char_save: AsyncMock,
    ctx: AppCtx,
    cvamp: cofd.Vampire,
    idx: int,
    count: int,
    expected: int | tuple[int, ...],
):
    toggler = Toggler(ctx, cvamp)
    adjuster = toggler.adjusters[3]
    assert isinstance(adjuster, VampAdjuster)

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)

    match idx:
        case 0 | 2:
            assert cvamp.vitae == expected
        case 3 | 5:
            assert isinstance(expected, tuple)
            mbp, bp = expected
            assert cvamp.max_vitae == mbp
            assert cvamp.vitae == bp
        case 6 | 8:
            assert isinstance(expected, tuple)
            gen, mbp = expected
            assert cvamp.blood_potency == gen
            assert cvamp.max_vitae == mbp

    assert mock_edit.await_count == count
    assert inter.response.edit_message.await_count == count
    inter.response.edit_message.assert_has_awaits([call(view=toggler)] * count)
    assert mock_char_save.await_count == count


@pytest.mark.parametrize(
    "idx,count,expected",
    [
        (0, 1, 7),
        (0, 100, 0),
        (2, 1, 9),
        (2, 100, 10),
    ],
)
async def test_mummy_sekhem_adjuster(
    mock_edit: AsyncMock,
    mock_char_save: AsyncMock,
    mummy_toggler: Toggler,
    idx: int,
    count: int,
    expected: int,
):
    adjuster = mummy_toggler.adjusters[3]
    assert isinstance(adjuster, MummySekhemAdjuster)

    inter = AsyncMock()
    inter.custom_id = adjuster.buttons[idx].custom_id

    for _ in range(count):
        await adjuster.callback(inter)

    assert mummy_toggler.character.sekhem == expected
    assert mock_edit.await_count == count
    assert inter.response.edit_message.await_count == count
    assert mock_char_save.await_count == count


@pytest.mark.parametrize(
    "rating,dec,inc",
    [
        (5, True, True),
        (10, True, False),
        (0, False, True),
    ],
)
def test_mummy_sekhem_button_states(mummy: cofd.Mummy, rating: int, dec: bool, inc: bool):
    mummy.sekhem = rating
    adj = MummySekhemAdjuster(AsyncMock(), mummy)
    assert adj.buttons[0].disabled == (not dec)
    assert adj.buttons[2].disabled == (not inc)


@pytest.mark.parametrize(
    "perm,temp,can_pdec,can_pinc,can_tdec,can_tinc",
    [
        (3, 2, True, True, True, True),
        (3, 3, True, True, True, False),
        (5, 5, True, False, True, False),
        (0, 0, False, True, False, False),
        (1, 0, True, True, False, True),
        (5, 1, True, False, True, True),
    ],
)
async def test_mummy_pillar_button_states(
    mummy: cofd.Mummy,
    perm: int,
    temp: int,
    can_pdec: bool,
    can_pinc: bool,
    can_tdec: bool,
    can_tinc: bool,
):
    # We don't need to test all of them, since they're the same class
    mummy.pillars[0].rating = perm
    mummy.pillars[0].temporary = temp
    mummy.pillars[1].rating = perm
    mummy.pillars[1].temporary = temp
    p = cofd.Mummy.Pillars
    adj = MummyPillarAdjuster(AsyncMock(), mummy, p.AB, p.BA)

    # We have two pillars, so we test the full range of buttons
    pdecs = (0, 6)
    for pdec in pdecs:
        assert adj.buttons[pdec].disabled == (not can_pdec)

    pincs = (2, 8)
    for pinc in pincs:
        assert adj.buttons[pinc].disabled == (not can_pinc)

    tdecs = (3, 9)
    for tdec in tdecs:
        assert adj.buttons[tdec].disabled == (not can_tdec)

    tincs = (5, 11)
    for tinc in tincs:
        assert adj.buttons[tinc].disabled == (not can_tinc)


@pytest.mark.parametrize(
    "pillar_name,ida,idx,count,expected",
    [
        # Permanent
        ("Ab", 4, 0, 1, 2),
        ("Ab", 4, 0, 10, 0),
        ("Ab", 4, 2, 1, 4),
        ("Ab", 4, 2, 10, 5),
        # Temporary
        ("Ab", 4, 3, 1, 2),
        ("Ab", 4, 3, 10, 0),
        ("Ab", 4, 5, 1, 3),
        ("Ab", 4, 5, 10, 3),  # Shouldn't exceed!
        # Permanent
        ("Ba", 4, 6, 1, 2),
        ("Ba", 4, 6, 10, 0),
        ("Ba", 4, 8, 1, 4),
        ("Ba", 4, 8, 10, 5),
        # Temporary
        ("Ba", 4, 9, 1, 2),
        ("Ba", 4, 9, 10, 0),
        ("Ba", 4, 11, 1, 3),
        ("Ba", 4, 11, 10, 3),  # Shouldn't exceed!
        # Permanent
        ("Ka", 5, 0, 1, 2),
        ("Ka", 5, 0, 10, 0),
        ("Ka", 5, 2, 1, 4),
        ("Ka", 5, 2, 10, 5),
        # Temporary
        ("Ka", 5, 3, 1, 2),
        ("Ka", 5, 3, 10, 0),
        ("Ka", 5, 5, 1, 3),
        ("Ka", 5, 5, 10, 3),  # Shouldn't exceed!
        # Permanent
        ("Ren", 5, 6, 1, 2),
        ("Ren", 5, 6, 10, 0),
        ("Ren", 5, 8, 1, 4),
        ("Ren", 5, 8, 10, 5),
        # Temporary
        ("Ren", 5, 9, 1, 2),
        ("Ren", 5, 9, 10, 0),
        ("Ren", 5, 11, 1, 3),
        ("Ren", 5, 11, 10, 3),  # Shouldn't exceed!
        # Permanent
        ("Sheut", 6, 0, 1, 2),
        ("Sheut", 6, 0, 10, 0),
        ("Sheut", 6, 2, 1, 4),
        ("Sheut", 6, 2, 10, 5),
        # Temporary
        ("Sheut", 6, 3, 1, 2),
        ("Sheut", 6, 3, 10, 0),
        ("Sheut", 6, 5, 1, 3),
        ("Sheut", 6, 5, 10, 3),  # Shouldn't exceed!
    ],
)
async def test_mummy_pillar_adjuster(
    mock_char_save: AsyncMock,
    mummy_toggler: Toggler,
    pillar_name: str,
    ida: int,
    idx: int,
    count: int,
    expected: tuple[int, int],
):
    adj = cast(MummyPillarAdjuster, mummy_toggler.adjusters[ida])
    if ida == 6:
        assert len(adj.pillars) == 1
    else:
        assert len(adj.pillars) == 2

    inter = AsyncMock()
    inter.custom_id = adj.buttons[idx].custom_id

    pillar = adj.character.get_pillar(pillar_name)
    temp = pillar.temporary

    for _ in range(count):
        await adj.callback(inter)

    if idx in (0, 2, 6, 8):  # Permanent rating
        assert pillar.rating == expected
        if idx in (0, 6):  # Decremented
            assert pillar.temporary == expected, "Temporary should have been reduced as well"
        else:  # Incremented
            assert pillar.temporary == temp
    else:
        assert pillar.temporary == expected

    mock_char_save.assert_awaited()


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
        (
            VampAdjuster,
            (5, 10, 10),
            {0: False, 2: False, 3: False, 5: False, 6: False, 8: False},
        ),
        (VampAdjuster, (0, 1, 3), {0: True, 2: False, 3: True, 5: False, 6: True, 8: False}),
        (VampAdjuster, (10, 10, 15), {0: False, 2: True, 3: False, 5: False, 6: False, 8: True}),
        (VampAdjuster, (10, 50, 3), {0: False, 2: False, 3: False, 5: True, 6: True, 8: False}),
    ],
)
def test_adjuster_button_states(
    vamp: wod.Vampire,
    cls: type[Adjuster],
    track: str | int | tuple[int, ...],
    expected: dict[int, bool],
):
    toggler = AsyncMock()
    if cls is HealthAdjuster:
        vamp.health = cast(str, track)
    elif cls is WillpowerAdjuster:
        vamp.willpower = cast(str, track)
    elif cls is GroundingAdjuster:
        vamp.grounding.rating = cast(int, track)
    elif cls is VampAdjuster:
        assert isinstance(track, tuple)
        bp, mbp, gen = track
        vamp.blood_pool = bp
        vamp.max_bp = mbp
        vamp.generation = gen  # We don't care about correctness of max BP here
    else:
        raise ValueError(f"Unexpected adjuster: {cls}")
    adjuster = cls(toggler, vamp)

    for idx, state in expected.items():
        assert adjuster.buttons[idx].disabled == state


@pytest.mark.parametrize(
    "vitae,max_vitae,potency,expected",
    [
        (0, 1, 0, {0: True, 2: False, 3: True, 5: False, 6: True, 8: False}),
        (5, 10, 5, {0: False, 2: False, 3: False, 5: False, 6: False, 8: False}),
        (75, 75, 10, {0: False, 2: True, 3: False, 5: True, 6: False, 8: True}),
    ],
)
def test_vtr_button_states(
    cvamp: cofd.Vampire,
    vitae: int,
    max_vitae: int,
    potency: int,
    expected: dict[int, bool],
):
    cvamp.vitae = vitae
    cvamp.max_vitae = max_vitae
    cvamp.blood_potency = potency

    adjuster = VampAdjuster(AsyncMock(), cvamp)
    for idx, state in expected.items():
        assert adjuster.buttons[idx].disabled == state

    pass


@patch("bot.AppCtx.respond", new_callable=AsyncMock)
async def test_adjust_command(mock_respond: AsyncMock, ctx: AppCtx, avamp: VampireType):
    await adjust(ctx, avamp)

    assert mock_respond.await_count == 2
    mock_respond.assert_has_awaits([call(embed=ANY), call(view=ANY, ephemeral=True)])


async def test_timeout(toggler: Toggler):
    mock_cmd_mention = Mock()
    mock_cmd_mention.return_value = "hello"
    toggler.ctx.bot.cmd_mention = mock_cmd_mention

    message_mock = AsyncMock()
    toggler.message = message_mock

    await toggler.on_timeout()

    mock_cmd_mention.assert_called_once_with("character adjust")
    message_mock.edit.assert_called_once_with(
        content="Adjustments timed out. Please run hello again.", view=None
    )


@pytest.mark.parametrize("err", [discord.NotFound, discord.Forbidden])
@patch("botchcord.character.adjust.Toggler.message", new_callable=AsyncMock)
async def test_timeout_error_handling(
    mock_message: AsyncMock, toggler: Toggler, err: type[Exception]
):
    mock_message.edit.side_effect = err(Mock(), "fake")
    try:
        await toggler.on_timeout()
    except (discord.Forbidden, discord.NotFound):
        pytest.fail("Exception should have been caught!")


async def test_select_adjuster(toggler: Toggler):
    new_selection = toggler.selector.options[1].label  # 0 is default

    # We can't programmatically set Select.values, so we have to mock it
    selector_mock = Mock()
    selector_mock.options = toggler.selector.options
    selector_mock.values = [new_selection]
    toggler.selector = selector_mock

    inter = AsyncMock()
    await toggler.select_adjuster(inter)
    inter.response.edit_message.assert_called_once_with(view=toggler)

    # Check that we've set the select
    assert not selector_mock.options[0].default
    assert selector_mock.options[1].default

    # Check that we've got the buttons
    adjuster = toggler.adjusters[1]
    for i, view_btn in enumerate(toggler.children[1:]):
        assert adjuster.buttons[i] == view_btn


def test_get_button_bad(toggler: Toggler):
    adjuster = toggler.adjusters[0]
    with pytest.raises(ValueError):
        adjuster.get_button("fake")


async def test_health_adjuster_unknown_row(toggler: Toggler):
    adjuster = toggler.adjusters[0]
    assert isinstance(adjuster, HealthAdjuster)

    button_mock = Mock()
    button_mock.row = 100
    get_button_mock = Mock()
    get_button_mock.return_value = (0, button_mock)
    adjuster.get_button = get_button_mock

    inter = AsyncMock()
    with pytest.raises(ValueError):
        await adjuster.callback(inter)
