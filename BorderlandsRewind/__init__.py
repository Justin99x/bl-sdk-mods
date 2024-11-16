from __future__ import annotations

import importlib
import sys
from typing import Any, List, TYPE_CHECKING

from Mods import ModMenu
from Mods.BorderlandsRewind.utilities import feedback, get_pc
from Mods.ModMenu import ClientMethod, Keybind, SDKMod, ServerMethod
from Mods.BorderlandsRewind.keybinds import KILL_NAME, blr_keybinds, local_set_skill_stacks
from Mods.BorderlandsRewind.options import BLROption, blr_options, local_handle_amp
from unrealsdk import FindObject, Log

if TYPE_CHECKING:
    from bl2 import SkillDefinition, WillowPlayerController


class BorderlandsRewind(SDKMod):
    Name: str = "Borderlands Rewind"
    Author: str = "Justin99"
    Description: str = "Enables glitches from early versions of the game"
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    def __init__(self):
        self.Options: List[BLROption] = blr_options
        self.Keybinds: List[Keybind] = blr_keybinds

    @ClientMethod
    def client_feedback(self, message, PC: WillowPlayerController = None):
        feedback(message)



    @ServerMethod
    def server_set_skill_stacks(self, skill_def_path: str, target_stacks: int, PC: WillowPlayerController = None):
        local_set_skill_stacks(skill_def_path, target_stacks, PC)
        self.client_feedback(f"Set {skill_def_path.split('.')[-1]} stacks to {target_stacks}", PC)

    @ServerMethod
    def server_handle_amp(self, enabled: bool, PC: WillowPlayerController = None):
        local_handle_amp(enabled, PC)

    def ModOptionChanged(self, option: BLROption, new_value: Any) -> None:
        option.on_change(new_value)

    def Enable(self) -> None:
        super().Enable()
        for option in self.Options:
            option.on_change(option.CurrentValue)
        Log(f"{self.Name} enabled")

    def Disable(self) -> None:
        super().Disable()
        for option in self.Options:
            option.on_change(False)
        Log(f"{self.Name} disabled")

instance = BorderlandsRewind()

if __name__ == "__main__":
    for submodule_name in ('keybinds', 'options', 'utilities'):
        module = sys.modules.get("Mods.BorderlandsRewind." + submodule_name)
        if module:
            importlib.reload(module)

    from Mods.BorderlandsRewind.keybinds import blr_keybinds
    from Mods.BorderlandsRewind.options import blr_options

    Log(f"[{instance.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break


ModMenu.RegisterMod(instance)

