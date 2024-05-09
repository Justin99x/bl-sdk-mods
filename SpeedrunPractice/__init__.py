import importlib
import inspect
import os
import sys
from typing import List, Optional

from Mods import ModMenu
from Mods.SpeedrunPractice.hooks import SPHooks
from Mods.SpeedrunPractice.keybinds import SPKeybind, SPKeybinds
from Mods.SpeedrunPractice.options import SPOptions
from Mods.SpeedrunPractice.utilities import RunCategory, PlayerClass, enum_from_value, get_current_player_controller
from unrealsdk import FindObject, Log

_DefaultGameInfo = FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")
_MODDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))
_CONFIG_PATH = os.path.join(_MODDIR, 'config.json')
_STATE_PATH = os.path.join(_MODDIR, 'state.json')


class SpeedrunPractice(ModMenu.SDKMod):
    Name: str = "Speedrun Practice"
    Author: str = "Justin99"
    Description: str = "Various utilities for practicing speedruns"
    Version: str = "1.5"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    Keybinds: List[SPKeybind]
    Options: List[ModMenu.Options.Base]

    def __init__(self):
        self.sp_options = SPOptions()
        self.sp_hooks = SPHooks()
        self.sp_keybinds = SPKeybinds(self.sp_options)

        self.Options = self.sp_options.Options
        self.Keybinds = self.sp_keybinds.Keybinds

        self.player_class: Optional[PlayerClass] = None
        self.run_category: Optional[RunCategory] = None

    def disable_all(self):
        self.sp_keybinds.disable()
        self.sp_hooks.disable()
        self.sp_options.disable()

    def enable_all(self):
        self.sp_options.enable(self.player_class, self.run_category)
        self.sp_hooks.enable(self.player_class, self.run_category)
        self.sp_keybinds.enable(self.player_class, self.run_category)

        self.Options = self.sp_options.Options
        self.Keybinds = self.sp_keybinds.Keybinds
        self.Keybinds.sort(key=lambda x: getattr(x, 'order', 100) + 1000 * int(x.IsHidden))  # Non-active keybinds de-prioritized

    def ModOptionChanged(self, option: ModMenu.Options.Base, new_value) -> None:
        """For anything that needs to be called on changing an option in the game menu."""

        option.CurrentValue = new_value  # Somehow needed to update original object.
        self.disable_all()
        if option == self.sp_options.RunCatOption:
            if self.player_class:
                self.sp_options.PlayerRunCategory.CurrentValue[self.player_class.value] = new_value
            self.run_category = enum_from_value(RunCategory, new_value)
        self.enable_all()

    @ModMenu.Hook('WillowGame.WillowGFxMovie.ShowAchievementsUI')
    def block_achievements(self, caller, function, params) -> bool:
        return False

    @ModMenu.Hook('WillowGame.WillowPlayerController.FinishSaveGameLoad')
    def load_character(self, caller, function, params) -> bool:
        if not params.SaveGame:
            return True
        self.disable_all()

        player_class_str = params.SaveGame.PlayerClassDefinition.Name
        self.player_class = enum_from_value(PlayerClass, player_class_str)
        self.run_category = enum_from_value(RunCategory, self.sp_options.PlayerRunCategory.CurrentValue.get(self.player_class.value))
        self.sp_options.RunCatOption.CurrentValue = self.run_category.value

        self.enable_all()
        return True

    def Enable(self) -> None:

        super().Enable()

        player_standin = FindObject("PlayerStandIn", "menumap.TheWorld:PersistentLevel.PlayerStandIn_2")
        PC = get_current_player_controller()
        if player_standin and player_standin.SaveGame:
            self.player_class = enum_from_value(PlayerClass, player_standin.SaveGame.PlayerClassDefinition.Name)
            self.run_category = enum_from_value(RunCategory, self.sp_options.PlayerRunCategory.CurrentValue.get(self.player_class.value))
            self.enable_all()
        elif PC and PC.PlayerClass:
            self.player_class = enum_from_value(PlayerClass, PC.PlayerClass.Name)
            self.run_category = enum_from_value(RunCategory, self.sp_options.PlayerRunCategory.CurrentValue.get(self.player_class.value))
            self.enable_all()

        Log("SpeedrunPractice Enabled")

    def Disable(self) -> None:
        self.disable_all()
        super().Disable()
        Log("SpeedrunPractice Disabled")


instance = SpeedrunPractice()

if __name__ == "__main__":
    for submodule_name in ('utilities', 'checkpoints', 'randomize_gear', 'skills', 'hooks', 'options', 'keybinds'):
        module = sys.modules.get("Mods.SpeedrunPractice." + submodule_name)
        # Log(module)
        if module:
            importlib.reload(module)

    # from Mods.SpeedrunPractice import utilities, checkpoints, randomize_gear, skills, hooks, options, keybinds
    from Mods.SpeedrunPractice.hooks import SPHooks
    from Mods.SpeedrunPractice.keybinds import SPKeybind, SPKeybinds
    from Mods.SpeedrunPractice.options import SPOptions
    from Mods.SpeedrunPractice.utilities import RunCategory, PlayerClass, enum_from_value, get_current_player_controller

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
