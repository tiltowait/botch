"""Character deletion command tests."""

from functools import partial
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

import pytest

import core
from bot import AppCtx
from botchcord.character.delete import DeletionModal, delete
from core.characters import GameLine, Splat
from tests.characters import gen_char

mk_char = partial(gen_char, line=GameLine.WOD, splat=Splat.VAMPIRE)


@pytest.mark.parametrize(
    "name,input,should_pass",
    [
        ("Billy", "billy", True),
        ("Billy", "Billy", True),
        ("Billy", "b", False),
    ],
)
async def test_deletion_modal(name: str, input: str, should_pass: bool):
    char = mk_char(name=name)
    modal = DeletionModal(char.name)
    assert len(f"Delete {char.name}?") < 45
    assert modal.title == f"Delete {char.name}?"

    modal.children[0].value = input
    inter = AsyncMock()
    await modal.callback(inter)
    assert modal.interaction == inter

    assert modal.should_delete == should_pass


@pytest.mark.parametrize("should_delete", [True, False])
@patch("botchcord.character.delete.DeletionModal")
async def test_delete(modal_mock: MagicMock, should_delete: bool):
    modal_instance = AsyncMock()
    modal_mock.return_value = modal_instance
    inter = AsyncMock()

    # Normally, it's callback() that sets the side effect, but delete() doesn't
    # call that function directly. For simplicity's sake, we put the side
    # effects in DeletionModal.wait().
    async def wait_side_effect():
        modal_instance.should_delete = should_delete
        modal_instance.interaction = inter

    modal_instance.wait.side_effect = wait_side_effect

    ctx = AppCtx(Mock(), AsyncMock())
    ctx.send_error = AsyncMock()

    char = mk_char(name="Billy")
    await core.cache.register(char)

    await delete(ctx, char)
    ctx.send_modal.assert_awaited_once_with(modal_instance)

    if should_delete:
        inter.respond.assert_awaited_once()
    else:
        ctx.send_error.assert_awaited_once_with(ANY, ANY, interaction=inter)
