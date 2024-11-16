from __future__ import annotations

from typing import Callable, TYPE_CHECKING, cast

from Mods.UserFeedback import TextInputBox
from unrealsdk import FindObject, GetEngine, Log

if TYPE_CHECKING:
    from bl2 import WillowPlayerController, WillowCoopGameInfo

_DefaultGameInfo: WillowCoopGameInfo | None = FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")


def get_pc() -> WillowPlayerController:
    """Returns the local player"""
    return cast('WillowPlayerController', GetEngine().GamePlayers[0].Actor)


def feedback(feedback: str) -> None:
    """Presents a "training" message to the user with the given string"""
    pc = get_pc()
    HUDMovie = pc.GetHUDMovie()
    if HUDMovie is None:
        return

    duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
    HUDMovie.ClearTrainingText()
    HUDMovie.AddTrainingText(feedback, "Borderlands Rewind", duration, (), "", False, 0, pc.PlayerReplicationInfo,
                             True)


def try_parse_int(s: str):
    try:
        return int(s)
    except ValueError:
        Log(f"Unable to parse input {s} to number, setting value to 0")
        return 0

def is_client() -> bool:
    return GetEngine().GetCurrentWorldInfo().NetMode == 3

def text_input_stacks(func: Callable[[str, int], None], title: str, ref: str = '') -> None:
    """Handle input box creation for various actions"""
    input_box = TextInputBox(title)
    pc = get_pc()

    def on_submit(msg: str) -> None:
        if msg:
            target_val = try_parse_int(msg)
            if target_val >= 0:
                func(ref, target_val)
            else:
                Log("Value must be greater than 0")

    input_box.OnSubmit = on_submit
    input_box.Show()
