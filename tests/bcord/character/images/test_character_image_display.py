"""Character image display tests."""

from random import randint
from typing import AsyncGenerator
from unittest.mock import ANY, AsyncMock, patch

import pytest

import core
import errors
from bot import AppCtx
from botchcord.character.images.display import ImagePager, display_images
from core.characters import Character, GameLine, Splat
from tests.characters import gen_char

NUM_IMAGES = 5


@pytest.fixture(autouse=True)
async def mock_api_delete() -> AsyncGenerator[AsyncMock, None]:
    with patch("api.delete_single_faceclaim", new_callable=AsyncMock) as mocked:
        mocked.return_value = True
        yield mocked


@pytest.fixture(scope="function")
async def char() -> AsyncGenerator[Character, None]:
    char = gen_char(GameLine.WOD, Splat.VAMPIRE)
    for _ in range(NUM_IMAGES):
        name = str(randint(1, 100000))
        url = f"https://pcs.botch.lol/fake/char/{name}.webp"
        char.profile.add_image(url)
    yield char


@pytest.fixture
def uinter() -> AsyncMock:
    """An interaction with user.id already set."""
    inter = AsyncMock()
    inter.user.id = 0
    return inter


@pytest.fixture(params=[0, 100])
def inters(request) -> AsyncMock:
    """Interactions with different users."""
    inter = AsyncMock()
    inter.user.id = request.param
    return inter


@pytest.fixture(params=[True, False])
async def pager(
    ctx: AppCtx,
    char: Character,
    request,
) -> ImagePager:
    return ImagePager(ctx, char, request.param)


async def test_char_images(char: Character):
    assert len(char.profile.images) == NUM_IMAGES
    assert char.profile.main_image == str(char.profile.images[0])


async def test_pager_counts(pager: ImagePager):
    assert len(pager.children) == 6
    assert pager.children == [
        pager.first_button,
        pager.prev_button,
        pager.indicator,
        pager.next_button,
        pager.last_button,
        pager.manage_button,
    ]
    assert len(pager.character.profile.images) == NUM_IMAGES
    assert pager.num_pages == len(pager.character.profile.images)


async def test_pager_one_image(ctx: AppCtx, character: Character):
    character.profile.add_image("https://pcs.botch.lol/fake/char/img.webp")
    pager = ImagePager(ctx, character, False)
    assert len(pager.children) == 1


async def test_basic_interaction_check(
    pager: ImagePager,
    inters: AsyncMock,
):
    # We haven't entered management mode
    if pager.invoker_controls:
        if inters.user.id != pager.ctx.user.id:
            assert not await pager.interaction_check(inters)
            inters.respond.assert_awaited_once_with(ANY, ephemeral=True)
        else:
            assert await pager.interaction_check(inters)


async def test_ic_in_management_mode(pager: ImagePager, inters: AsyncMock):
    pager.management_mode = True

    if inters.user.id == pager.ctx.user.id:
        assert await pager.interaction_check(inters)
        inters.respond.assert_not_awaited()
    else:
        assert not await pager.interaction_check(inters)
        inters.respond.assert_awaited_once_with(
            "You may only manage your own characters' images.", ephemeral=True
        )


async def test_enter_management_mode(pager: ImagePager, inters: AsyncMock):
    inters.custom_id = pager.manage_button.custom_id
    if inters.user.id == pager.character.user:
        assert await pager.interaction_check(inters)
        inters.respond.assert_not_awaited()
    else:
        assert not await pager.interaction_check(inters)
        inters.respond.assert_awaited_once_with(
            "You may only manage your own characters' images.", ephemeral=True
        )


@pytest.mark.parametrize("children", [True, False])
async def test_timeout(pager: ImagePager, children: bool):
    pager.message = AsyncMock()
    if children:
        await pager.on_timeout()
        pager.message.edit.assert_awaited_once_with(view=None)
    else:
        pager.clear_items()
        await pager.on_timeout()
        pager.message.edit.assert_not_awaited()


# For the paging tests, button ownership is in test_interaction_check()


@pytest.mark.parametrize("direction", ["forward", "backward"])
async def test_basic_paging(pager: ImagePager, uinter: AsyncMock, direction: str):
    def assert_embed(page: int):
        assert pager.current_page == page
        assert pager.embed.image
        assert pager.embed.image.url == pager.current_image
        assert pager.indicator.label == f"{page + 1}/{pager.num_pages}"

        if page == 0:
            assert pager.first_button.disabled
        elif page == pager.num_pages - 1:
            assert pager.last_button.disabled

    assert_embed(0)

    if direction == "forward":
        action = pager.next_page
        pages = list(range(1, pager.num_pages)) + [0]  # Test wrapping to 0
    else:
        action = pager.previous_page
        pages = list(range(pager.num_pages - 1, 0, -1)) + [0]

    for page in pages:
        await action(uinter)
        uinter.response.edit_message.assert_awaited_with(embed=ANY, view=pager)
        assert_embed(page)

    assert uinter.response.edit_message.await_count == pager.num_pages
    assert uinter.response.edit_message.await_count == len(pages)


async def test_first_last(pager: ImagePager, uinter: AsyncMock):
    def assert_embed(page: int):
        assert pager.current_page == page
        assert pager.embed.image
        assert pager.embed.image.url == pager.current_image
        assert pager.indicator.label == f"{page + 1}/{pager.num_pages}"

        if page == 0:
            assert pager.first_button.disabled
        elif page == pager.num_pages - 1:
            assert pager.last_button.disabled

    assert_embed(0)

    await pager.last_page(uinter)
    assert pager.last_button.disabled
    uinter.response.edit_message.assert_awaited_with(embed=ANY, view=pager)
    assert_embed(pager.num_pages - 1)

    await pager.first_page(uinter)
    assert pager.first_button.disabled
    uinter.response.edit_message.assert_awaited_with(embed=ANY, view=pager)
    assert_embed(0)

    assert uinter.response.edit_message.await_count == 2


# Management
# Like before, we already tested the button eligibility


async def test_management_mode(pager: ImagePager, uinter: AsyncMock):
    assert len(pager.children) == 6
    await pager.goto_page(3, uinter)
    assert pager.current_page == 3

    image = pager.current_image  # We will promote this

    await pager.mode_toggle(uinter)
    assert pager.management_mode
    assert pager.children == [
        pager.promote_button,
        pager.demote_button,
        pager.delete_button,
        pager.cancel_button,
    ]
    uinter.response.edit_message.assert_awaited_with(view=pager)

    await pager._promote_image(uinter)
    assert pager.current_page == 0
    assert pager.current_image == image
    assert str(pager.character.profile.images[0]) == image

    assert pager.character.save.await_count == 1

    await pager._demote_image(uinter)
    assert pager.current_page == pager.num_pages - 1
    assert pager.current_image == image
    assert str(pager.character.profile.images[-1]) == image

    assert pager.character.save.await_count == 2

    await pager._delete_image(uinter)
    assert pager.current_page == pager.num_pages - 1, "Should still be on last page"
    assert image not in map(str, pager.character.profile.images)
    assert pager.num_pages == NUM_IMAGES - 1
    assert pager.indicator.label == f"{NUM_IMAGES - 1}/{NUM_IMAGES - 1}"

    assert pager.character.save.await_count == 3

    await pager.mode_toggle(uinter)
    assert pager.children == [
        pager.first_button,
        pager.prev_button,
        pager.indicator,
        pager.next_button,
        pager.last_button,
        pager.manage_button,
    ]

    assert uinter.response.edit_message.await_count == 6


# All that ... just to test the display command in < 10 lines


async def test_display_images(ctx: AppCtx, char: Character):
    await display_images(ctx, char, False)
    ctx.respond.assert_awaited_once_with(embed=ANY, view=ANY)


async def test_display_no_images(ctx: AppCtx, character: Character):
    await core.cache.register(character)
    with pytest.raises(errors.CharacterIneligible):
        await display_images(ctx, character.name, False)
    ctx.respond.assert_not_awaited()
    await core.cache.remove(character)
