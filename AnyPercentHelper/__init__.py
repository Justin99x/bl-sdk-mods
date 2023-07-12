
import importlib
import inspect
import os

import unrealsdk
import Mods
from Mods import ModMenu
from Mods.Commander import _ApplyPosition, _GetPosition
from Mods.UserFeedback import TextInputBox
from Mods.AnyPercentHelper.checkpoints import CheckpointSaver, SaveNameInput
from Mods.AnyPercentHelper.glitch_manager import GlitchManager
from Mods.AnyPercentHelper.utilities import Utilities
from Mods.AnyPercentHelper.randomize_gear import GearRandomizer

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")
_MODDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))
_CONFIG_PATH = os.path.join(_MODDIR, 'config.json')
_STATE_PATH = os.path.join(_MODDIR, 'state.json')


class AnyPercentHelper(ModMenu.SDKMod):
    Name: str = "Any% Helper"
    Author: str = "Justin99"
    Description: str = "Various utilities for practicing Any% speedruns on current patch"
    Version: str = "1.3.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    Keybinds = [
        ModMenu.Keybind("Add Buckup Stack", "None"),
        ModMenu.Keybind("Remove Buckup Stack", "None"),
        ModMenu.Keybind("Add 10 Anarchy Stacks", "None"),
        ModMenu.Keybind("Add Free Shot Stack", "None"),
        ModMenu.Keybind("Remove Free Shot Stack", "None"),
        ModMenu.Keybind("Merge Equipped Weapons", "None"),
        ModMenu.Keybind("Save Checkpoint", "None"),
        ModMenu.Keybind("Load Checkpoint State", "None"),
        ModMenu.Keybind("Show Stacks/Crit", "None"),
        ModMenu.Keybind("Randomize Gear!", "None")
    ]

    def GameInputPressed(self, input) -> None:
        """Handle methods that need the class instance here"""
        glitches = GlitchManager()

        if input.Name == "Add Buckup Stack":
            glitches.add_buckup_stack()
        elif input.Name == "Remove Buckup Stack":
            glitches.remove_buckup_stack()
        elif input.Name == "Add 10 Anarchy Stacks":
            glitches.add_10_anarchy_stacks()
        elif input.Name == "Add Free Shot Stack":
            glitches.add_infinite_ammo_stack()
        elif input.Name == "Remove Free Shot Stack":
            glitches.remove_infinite_ammo_stack()
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
        self.block_deactivate_half_ammo = False
        self.FullAmpDamageBoolean = ModMenu.Options.Boolean(
            Caption="Full Amp Damage",
            Description="Applies full amp damage to every projectile on multi-projectile weapons",
            StartingValue=True,
            Choices=("Off", "On")
        )
        self.WeaponMerging = ModMenu.Options.Boolean(
            Caption="Weapon Merging",
            Description="Allows weapon merging to stack bonuses from multiple weapons",
            StartingValue=True,
            Choices=("Off", "On")
        )
        self.VladofInfiniteAmmo = ModMenu.Options.Boolean(
            Caption="Infinite Ammo Stacking",
            Description="Allows using a Vladof launcher to stack infinite ammo",
            StartingValue=True,
            Choices=("Off", "On")
        )
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
            self.FullAmpDamageBoolean,
            self.WeaponMerging,
            self.VladofInfiniteAmmo,
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
            Utilities.get_current_player_controller().ConsoleCommand(f"set GD_Globals.General.Globals PickupRadius 200")
        return True

    @ModMenu.Hook("Engine.Actor.TriggerGlobalEventClass")
    def load_previous_equipped_weapon(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                      params: unrealsdk.FStruct) -> bool:
        """Bypasses usual behavior or 2nd weapon picked up being equipped on load"""
        if params.InEventClass.Name == 'WillowSeqEvent_PlayerJoined':
            checkpoint_saver = CheckpointSaver(None)
            game_state = checkpoint_saver.get_game_state_from_state_file()
            if game_state:
                checkpoint_saver.PC.EquipWeaponFromSlot(game_state['active_weapon'])
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
        """Enables Three Horns Divide FT as soon as Sanctuary is reached, allows skipping station like in patch 1.1"""
        if 'Sanctuary' in caller.ActivatedTeleportersList and 'IceEast' not in caller.ActivatedTeleportersList:
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

        # Just set to 1 if option is turned off
        if not self.FullAmpDamageBoolean.CurrentValue:
            projectiles = 1
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

    @ModMenu.Hook('WillowGame.WillowWeapon.RemoveAllExternalAttributeEffects')
    def allow_weapon_merging(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                             params: unrealsdk.FStruct) -> bool:
        """
        Allow merging weapons to keep crit bonuses, healing, etc. Just block removing attribute effects when changing
        weapons in inventory and a pending weapon exists (happens when entering inventory mid-swap)
        """
        if not self.WeaponMerging.CurrentValue:
            return True
        PC = Utilities.get_current_player_controller()
        inv_manager = PC.GetPawnInventoryManager()

        if PC.bStatusMenuOpen and inv_manager.PendingWeapon:
            return False
        return True

    """
    Next 3 hooks are all to replicate infinite ammo glitch from Vladof launcher. Don't have enough information in
    just the deactivate skill hook to tell whether to block it or not. We're looking for whether we just equipped or
    just dropped the weapon, in which case we block the deactivation. The drop is due to the method being called twice
    for some unknown reason.
    """

    @ModMenu.Hook('WillowGame.WillowInventoryManager.RemoveFromInventory')
    def set_dropped_vladof_flag(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                params: unrealsdk.FStruct) -> bool:
        """Block if gun dropped"""
        if params.ItemToRemove.Class.Name == 'WillowWeapon' and params.ItemToRemove.DefinitionData.WeaponTypeDefinition.Name == 'WT_Vladof_Launcher':
            self.block_deactivate_half_ammo = True
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.OnEquip')
    def set_equipped_vladof_flag(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                 params: unrealsdk.FStruct) -> bool:
        """Block on equip."""
        if caller.DefinitionData.WeaponTypeDefinition.Name == 'WT_Vladof_Launcher':
            self.block_deactivate_half_ammo = True
        return True

    @ModMenu.Hook('WillowGame.SkillEffectManager.DeactivateSkill')
    def block_deactivate_free_shot(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                   params: unrealsdk.FStruct) -> bool:
        """Block when the flag is set and reset the flag."""
        if not self.VladofInfiniteAmmo.CurrentValue:
            self.block_deactivate_half_ammo = False
            return True
        if params.Definition.Name == 'Skill_VladofHalfAmmo':
            if self.block_deactivate_half_ammo:
                self.block_deactivate_half_ammo = False
                return False
        return True

    def Enable(self) -> None:
        super().Enable()
        unrealsdk.Log("AnyPercentHelper Enabled")

    def Disable(self) -> None:
        unrealsdk.Log("AnyPercentHelper Disabled")
        super().Disable()


instance = AnyPercentHelper()

if __name__ == "__main__":
    importlib.reload(Mods.AnyPercentHelper.utilities)
    importlib.reload(Mods.AnyPercentHelper.glitch_manager)
    importlib.reload(Mods.AnyPercentHelper.checkpoints)
    importlib.reload(Mods.AnyPercentHelper.randomize_gear)
    from Mods.AnyPercentHelper.checkpoints import CheckpointSaver, SaveNameInput
    from Mods.AnyPercentHelper.glitch_manager import GlitchManager
    from Mods.AnyPercentHelper.utilities import Utilities
    from Mods.AnyPercentHelper.randomize_gear import GearRandomizer


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
