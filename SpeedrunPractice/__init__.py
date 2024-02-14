import importlib
import inspect
import os
from typing import Callable

import unrealsdk
import Mods
from Mods import ModMenu

from Mods.UserFeedback import TextInputBox
from Mods.SpeedrunPractice.checkpoints import CheckpointSaver, SaveNameInput
from Mods.SpeedrunPractice.glitch_manager import GlitchManager
from Mods.SpeedrunPractice.utilities import Utilities
from Mods.SpeedrunPractice.randomize_gear import GearRandomizer

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")
_MODDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))
_CONFIG_PATH = os.path.join(_MODDIR, 'config.json')
_STATE_PATH = os.path.join(_MODDIR, 'state.json')


class SpeedrunPractice(ModMenu.SDKMod):
    Name: str = "Speedrun Practice"
    Author: str = "Justin99"
    Description: str = "Various utilities for practicing speedruns on current patch"
    Version: str = "1.4.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    Keybinds = [
        ModMenu.Keybind("Set Buckup Stacks", "None"),
        ModMenu.Keybind("Set Anarchy Stacks", "None"),
        ModMenu.Keybind("Set Free Shot Stacks", "None"),
        ModMenu.Keybind("Set Smasher Chance Stacks", "None"),
        ModMenu.Keybind("Set Smasher SMASH Stacks", "None"),
        ModMenu.Keybind("Merge Equipped Weapons", "None"),
        ModMenu.Keybind("Save Checkpoint", "None"),
        ModMenu.Keybind("Load Checkpoint State", "None"),
        ModMenu.Keybind("Show Stacks/Crit", "None"),
        ModMenu.Keybind("Randomize Gear!", "None")
    ]

    def handle_stacks(self, func: Callable[[int, str], None], title: str, ref: str = '') -> None:
        """Handle input box creation for various actions"""
        input_box = TextInputBox(title, PausesGame=True)

        def OnSubmit(msg: str) -> None:
            target_val = Utilities.try_parse_int(msg)
            if target_val >= 0:
                func(target_val, ref)
            else:
                unrealsdk.Log("1")
                Utilities.feedback("Value must be greater than 0")

        input_box.OnSubmit = OnSubmit
        input_box.Show()

    def GameInputPressed(self, input) -> None:
        """Handle methods that need the class instance here"""
        glitches = GlitchManager()

        if input.Name == "Set Buckup Stacks":
            self.handle_stacks(glitches.set_skill_stacks, input.Name, "GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player")
        elif input.Name == "Set Anarchy Stacks":
            self.handle_stacks(glitches.set_anarchy_stacks, input.Name)
        elif input.Name == "Set Free Shot Stacks":
            self.handle_stacks(glitches.set_skill_stacks, input.Name, "GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo")
        elif input.Name == "Set Smasher Chance Stacks":
            self.handle_stacks(glitches.set_skill_stacks, input.Name, "GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher")
        elif input.Name == "Set Smasher SMASH Stacks":
            self.handle_stacks(glitches.set_skill_stacks, input.Name, "GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher_SMASH")
        elif input.Name == "Merge Equipped Weapons":
            glitches.merge_all_equipped_weapons()
        elif input.Name == "Save Checkpoint":
            save_name_input = SaveNameInput("Character Save Name", PausesGame=True)
            save_name_input.Show()
        elif input.Name == "Load Checkpoint State":
            checkpoint_saver = CheckpointSaver(None)
            checkpoint_saver.load_game_state()
        elif input.Name == "Show Stacks/Crit":
            glitches.show_state()
        elif input.Name == "Randomize Gear!":
            gear_randomizer = GearRandomizer()
            gear_randomizer.randomize_gear()


    def __init__(self):
        self.expansions = []
        self.block_remove_attribute = False
        self.JakobsAutoFire = ModMenu.Options.Boolean(
            Caption="Automatic Jakobs Shotguns",
            Description="Makes Jakobs shotguns automatic to mimic freescroll macro functionality",
            StartingValue=False,
            Choices=("Off", "On")
        )
        self.DisableExpansionTravel = ModMenu.Options.Boolean(
            Caption="Disable Expansion Travel",
            Description="Removes expansion locations from Fast Travel menus",
            StartingValue=False,
            Choices=("Off", "On")
        )
        self.Options = [
            self.JakobsAutoFire,
            self.DisableExpansionTravel,
        ]

    def ModOptionChanged(self, option: ModMenu.Options.Base, new_value) -> None:
        """For anything that needs to be called on changing an option in the game menu"""
        if option == self.JakobsAutoFire:
            glitches = GlitchManager()
            glitches.handle_jakobs_auto(new_value)
        if option == self.DisableExpansionTravel:
            self.handle_expansion_fast_travel()

    @ModMenu.Hook("Engine.Actor.TriggerGlobalEventClass")
    def set_pickup_radius(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                          params: unrealsdk.FStruct) -> bool:
        """Mimic version 1.1 behavior on bulk pickup radius"""
        if params.InEventClass.Name == 'WillowSeqEvent_PlayerJoined':
            PC = Utilities.get_current_player_controller()
            PC.ConsoleCommand(f"set GD_Globals.General.Globals PickupRadius 200")
            PC.ConsoleCommand(f"set Behavior_ActivateSkill bNoSkillStacking False")
        return True

    def handle_expansion_fast_travel(self):
        """ Remove expansions from DLC manager so that they don't show up in FT. Add them back in if the option is
        turned back off."""
        dlc_manager = unrealsdk.GetEngine().GetDLCManager()
        if self.DisableExpansionTravel.CurrentValue:
            if len(dlc_manager.Expansions) > 0:
                for expansion in dlc_manager.Expansions:
                    self.expansions.append(expansion)
                dlc_manager.Expansions = []
        else:
            if len(dlc_manager.Expansions) == 0 and len(self.expansions) > 0:
                dlc_manager.Expansions = self.expansions  # This makes a copy since Expansions is FArray and not a list
                self.expansions = []

    @ModMenu.Hook('WillowGame.WillowDownloadableContentManager.HasCompatibilityData')
    def hook_dlc_manager(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                         params: unrealsdk.FStruct) -> bool:
        """Hooking this function to get FT updated when BL2 is first started."""
        self.handle_expansion_fast_travel()
        return True

    @ModMenu.Hook('WillowGame.WillowPlayerController.SaveGame')
    def enable_divide_fast_travel(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                  params: unrealsdk.FStruct) -> bool:
        """Enables Three Horns Divide FT as soon as Divide mission reached, allows skipping station like in patch 1.1"""
        if 'IceEast' not in caller.ActivatedTeleportersList:
            if caller.GetActivePlotCriticalMissionNumber() >= 4:
                temp = list(caller.ActivatedTeleportersList)
                temp.append('IceEast')
                caller.ActivatedTeleportersList = temp
        return True

    def _apply_full_amp(self, active_weapon, impact_shield_skill):
        """
        Apply full amp damage to every pellet. We replace the skill scale constant with the
        projectile count to effectively give every pellet full amp damage. Won't work with Gunzerk probably.
        """
        projectiles_attr = unrealsdk.FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponProjectilesPerShot")
        projectiles = projectiles_attr.GetValue(active_weapon)[0]

        weapon_damage_effect = [effect for effect in impact_shield_skill.SkillEffects if
                                effect.EffectData.AttributeToModify.Name == "WeaponDamage"][0]

        weapon_damage_effect.EffectData.BaseModifierValue.BaseValueScaleConstant = projectiles
        return

    @ModMenu.Hook('WillowGame.Skill.Resume')
    def amp_on_skill_resume(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                            params: unrealsdk.FStruct) -> bool:
        """Adjust damage bonus any time the skill is resumed."""
        if caller.Definition.Name not in ['Impact_Shield_Skill_Legendary', 'Impact_Shield_Skill']:
            return True
        PC = Utilities.get_current_player_controller()
        active_weapon = PC.GetActiveOrBestWeapon()
        self._apply_full_amp(active_weapon, caller)
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.OnEquip')
    def amp_on_equip(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                     params: unrealsdk.FStruct) -> bool:
        """Adjust damage bonus when swapping to a new weapon with full shield
        since it may have a different projectile count."""
        PC = Utilities.get_current_player_controller()
        if caller != PC.GetActiveOrBestWeapon():
            return True
        impact_skill_names = ['Impact_Shield_Skill_Legendary', 'Impact_Shield_Skill']

        # Get impact shield skills. Sometimes there can be paused skills that never go away, so we only
        # want to apply to active skills. The Skill.Resume() hook will cover any we missed.
        glitches = GlitchManager()
        impact_shield_skills = glitches.get_skill_stacks(impact_skill_names)
        for skill in impact_shield_skills:
            if skill.SkillState == 1:
                self._apply_full_amp(caller, skill)
        return True

    @ModMenu.Hook('WillowGame.WillowPlayerController.ModalGameMenuOpening')
    def hook_menu_open(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """Allow merging weapons to keep crit bonuses, healing, etc. This follows the exact logic that made
        the glitch possible in the first place. They later added the ForePutDownInactiveWeapon call to the
        ModalGameMenuOpening method to fix it, so we're just blocking it."""

        def block_putdown(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False

        unrealsdk.RunHook('WillowGame.WillowWeapon.ForcePutDownInactiveWeapon', 'block_putdown', block_putdown)
        caller.ModalGameMenuOpening()
        unrealsdk.RemoveHook('WillowGame.WillowWeapon.ForcePutDownInactiveWeapon', 'block_putdown')
        return False

    @ModMenu.Hook('WillowGame.WillowInventoryManager.RemoveFromInventory')
    def hook_remove_from_inventory(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                   params: unrealsdk.FStruct) -> bool:
        """Allow dropping weapons to keep skill stacks. This follows the exact logic that made
        the glitch possible in the first place. They later added the OnUnequip call to the
        RemoveFromInventory method to fix it, so we're just blocking it."""

        def block_onunequip(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False

        unrealsdk.RunHook('WillowGame.WillowWeapon.OnUnequip', 'block_onunequip', block_onunequip)
        caller.RemoveFromInventory(params.ItemToRemove, params.bCanDrop)
        unrealsdk.RemoveHook('WillowGame.WillowWeapon.OnUnequip', 'block_onunequip')
        return False

    def Enable(self) -> None:
        super().Enable()
        unrealsdk.Log("SpeedrunPractice Enabled")

    def Disable(self) -> None:
        unrealsdk.Log("SpeedrunPractice Disabled")
        super().Disable()


instance = SpeedrunPractice()

if __name__ == "__main__":
    importlib.reload(Mods.SpeedrunPractice.utilities)
    importlib.reload(Mods.SpeedrunPractice.glitch_manager)
    importlib.reload(Mods.SpeedrunPractice.checkpoints)
    importlib.reload(Mods.SpeedrunPractice.randomize_gear)
    from Mods.SpeedrunPractice.checkpoints import CheckpointSaver, SaveNameInput
    from Mods.SpeedrunPractice.glitch_manager import GlitchManager
    from Mods.SpeedrunPractice.utilities import Utilities
    from Mods.SpeedrunPractice.randomize_gear import GearRandomizer

    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break

ModMenu.RegisterMod(instance)
