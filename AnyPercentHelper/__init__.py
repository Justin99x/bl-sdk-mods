import hashlib
import inspect
import json
import os
import stat
from typing import cast

import unrealsdk
from Mods.Commander import _ApplyPosition, _GetPosition
from Mods import ModMenu

from Mods.UserFeedback import TextInputBox

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")
_MODDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))
_CONFIG_PATH = os.path.join(_MODDIR, 'config.json')
_STATE_PATH = os.path.join(_MODDIR, 'state.json')


class Utilities:
    """Class for organizing various useful methods"""

    @staticmethod
    def get_save_dir_from_config():
        with open(_CONFIG_PATH, "r") as f:
            config = json.load(f)
        return config["LocalGameSaves"]

    @staticmethod
    def get_current_player_controller() -> unrealsdk.UObject:
        """Returns the local player"""
        return cast(unrealsdk.UObject, unrealsdk.GetEngine().GamePlayers[0].Actor)

    @staticmethod
    def clone_obj(new_name, in_class_str, template_obj_str):
        """Creates a fresh object based on the class name and a template object defintion"""
        obj_to_clone = unrealsdk.FindObject(in_class_str, template_obj_str)
        return unrealsdk.ConstructObject(Class=in_class_str, Outer=obj_to_clone.Outer, Name=new_name,
                                         Template=obj_to_clone)

    @staticmethod
    def get_hash(filepath):
        with open(filepath, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.new("sha256", file_contents).hexdigest()

        return file_hash

    @classmethod
    def feedback(cls, feedback):
        """Presents a "training" message to the user with the given string"""
        PC = cls.get_current_player_controller()
        HUDMovie = PC.GetHUDMovie()
        if HUDMovie is None:
            return

        duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
        HUDMovie.ClearTrainingText()
        HUDMovie.AddTrainingText(feedback, "Gaige Any% Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                                 True)


class Glitches:
    """Class for applying stacks (buck up, anarchy, etc.) arbitrarily"""

    def __init__(self):
        self.PC = Utilities.get_current_player_controller()
        self.skill_manager = self.PC.GetSkillManager()
        self.inventory_manager = self.PC.GetPawnInventoryManager()
        self.anarchy_attribute_def = unrealsdk.FindObject("DesignerAttributeDefinition",
                                                          "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")
        self.anarchy_max_stacks_attribute_def = unrealsdk.FindObject("DesignerAttributeDefinition",
                                                                     "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_StackCap")
        self.autoburst_attribute_def = unrealsdk.FindObject("AttributeDefinition",
                                                            "D_Attributes.Weapon.WeaponAutomaticBurstCount")
        self.crititical_hit_bonus_attribute_def = unrealsdk.FindObject("AttributeDefinition",
                                                                       "D_Attributes.GameplayAttributes.PlayerCriticalHitBonus")

    def get_skill_stacks(self, skill_names: list):
        """Get SkillDefinition objects for active skills matching the name"""
        return [skill.Definition for skill in self.skill_manager.ActiveSkills if
                skill.Definition.SkillName in skill_names]

    def _add_skill_definition_instance(self, skill_msg_name, template_obj_str):
        """Create new activated instance of skill definition"""
        cloned_skill = Utilities.clone_obj(skill_msg_name, 'SkillDefinition', template_obj_str)
        old_stacks = len(self.get_skill_stacks([cloned_skill.SkillName]))
        self.skill_manager.ActivateSkill(self.PC, cloned_skill)
        Utilities.feedback(f"Current {skill_msg_name} stacks: {old_stacks + 1}")

    def _remove_skill_definition_instance(self, skill_msg_name, skill_name):
        """Remove one instance of skill definition"""
        skill_stacks = self.get_skill_stacks([skill_name])
        old_stacks = len(skill_stacks)
        if skill_stacks:
            self.skill_manager.DeactivateSkill(self.PC, skill_stacks[0])
            Utilities.feedback(f"Current {skill_msg_name} stacks: {old_stacks - 1}")
            return
        Utilities.feedback(f"No {skill_msg_name} stacks available to remove")

    def add_buckup_stack(self) -> None:
        """Add one 'stack' of Buck Up"""
        self._add_skill_definition_instance('Buck Up', 'GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player')

    def remove_buckup_stack(self) -> None:
        """Remove one 'stack' of Buck Up"""
        self._remove_skill_definition_instance('Buck Up', 'ShieldProbeBoost')

    def set_buckup_stacks(self, target_stacks: int) -> None:
        """Set stacks of Buck Up to desired value"""
        current_stacks = len(self.get_skill_stacks(['ShieldProbeBoost']))
        for i in range(current_stacks):
            self.remove_buckup_stack()
        for i in range(target_stacks):
            self.add_buckup_stack()
        Utilities.feedback(f"Current Buck Up stacks: {target_stacks}")

    def add_infinite_ammo_stack(self) -> None:
        """Remove one 'stack' of infinite ammo"""
        self._add_skill_definition_instance('Vladof Free Shot', 'GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo')

    def remove_infinite_ammo_stack(self) -> None:
        """Remove one 'stack' infinite ammo"""
        self._remove_skill_definition_instance('Vladof Free Shot', 'Vladof Half Ammo')

    def set_infinite_ammo_stacks(self, target_stacks: int) -> None:
        """Set stacks of infinite ammo to desired value"""
        current_stacks = len(self.get_skill_stacks(['Vladof Half Ammo']))
        for i in range(current_stacks):
            self.remove_infinite_ammo_stack()
        for i in range(target_stacks):
            self.add_infinite_ammo_stack()
        Utilities.feedback(f"Current free shot stacks: {target_stacks}")

    def get_anarchy_stacks(self) -> int:
        """Get stacks of anarchy from the attribute definition"""
        return int(self.anarchy_attribute_def.GetValue(self.PC)[0])

    def add_10_anarchy_stacks(self) -> None:
        """Add 10 stacks of anarchy, but only up to the maximum value"""
        max_stacks = self.anarchy_max_stacks_attribute_def.GetValue(self.PC)[0]
        current_stacks = self.anarchy_attribute_def.GetValue(self.PC)[0]
        self.anarchy_attribute_def.SetAttributeBaseValue(self.PC, min(current_stacks + 10, max_stacks))

    def set_anarchy_stacks(self, target_stacks):
        """Set anarchy stacks to desired value. Can go over the max using this."""
        self.anarchy_attribute_def.SetAttributeBaseValue(self.PC, target_stacks)

    def merge_all_equipped_weapons(self) -> None:
        """Applies external attribute effects from all weapons currently equipped. Used for crit bonus in Any% runs."""
        weapons = self.inventory_manager.GetEquippedWeapons()
        msg = ''
        for weapon in weapons:
            if weapon:
                weapon.ApplyAllExternalAttributeEffects()
                msg = msg + '\n' + weapon.GetShortHumanReadableName()
        Utilities.feedback(f"Bonuses from the following weapons are applied: {msg}")

    def handle_jakobs_auto(self, new_value: bool):
        """Turns automatic Jakobs shotguns on or off. Used to mimic functionality of free scroll macro."""
        weapons = unrealsdk.FindAll('WillowWeapon')
        jakobs_shotguns = [weapon for weapon in weapons if
                           weapon.DefinitionData.WeaponTypeDefinition is not None and weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun']
        if new_value:
            self.PC.ConsoleCommand(
                f"set WeaponTypeDefinition'GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun' AutomaticBurstCount 0")
            for js in jakobs_shotguns:
                self.autoburst_attribute_def.SetAttributeBaseValue(js, 0)
        else:
            self.PC.ConsoleCommand(
                f"set WeaponTypeDefinition'GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun' AutomaticBurstCount 1")
            for js in jakobs_shotguns:
                self.autoburst_attribute_def.SetAttributeBaseValue(js, 1)

    def show_state(self):
        """Show current status of key values"""
        msg = f"Buckup Stacks: {len(self.get_skill_stacks(['ShieldProbeBoost']))}"
        msg += f"\nFree Shot Stacks: {len(self.get_skill_stacks(['Vladof Half Ammo']))}"
        msg += f"\nCritical Hit Bonus: {round(self.crititical_hit_bonus_attribute_def.GetValue(self.PC)[0], 2)}"
        Utilities.feedback(msg)


class CheckpointSaver:
    """Class for saving read only copy of the current game and saving key values in local state.json file."""

    def __init__(self, new_save_name):
        self.PC = Utilities.get_current_player_controller()
        self.new_save_name = new_save_name
        self.save_dir = Utilities.get_save_dir_from_config()
        self.current_file_name = self.PC.GetWillowGlobals().GetWillowSaveGameManager().LastLoadedFilePath
        self.current_file_path = self.get_current_file_path()
        self.temp_file_path = self.get_temp_file_path()
        self.new_file_path = self.get_next_open_save_path()
        self.glitches = Glitches()

    def get_current_file_path(self) -> str:
        """Current file path based on save directory and game provided filename. Will fail if config.json not
        set correctly."""
        current_file_path = os.path.join(self.save_dir, self.current_file_name)
        if not (os.path.exists(current_file_path) and os.path.isfile(current_file_path)):
            Utilities.feedback("Error finding current filepath")
            raise FileNotFoundError("Error finding current filepath")
        return current_file_path

    def get_temp_file_path(self) -> str:
        """Temp file path to rename current save."""
        temp_file_path = os.path.join(self.save_dir, "temp.sav")
        if os.path.exists(temp_file_path):
            os.chmod(temp_file_path, stat.S_IWRITE)
            os.remove(temp_file_path)
        return temp_file_path

    def get_next_open_save_path(self):
        """Finds next available save number based on files in the save directory. Increments by 1."""

        path_num = int(self.current_file_name[4:8], 16)
        while True:
            path_num = path_num+1

            filepath = f"Save{path_num:x}".zfill(4).upper() + ".sav"
            if not os.path.exists(os.path.join(self.save_dir, filepath)):
                break
        return os.path.join(self.save_dir, filepath)

    def save_game_copy(self):
        """Saves current game state as read only, preserving previous file."""
        os.chmod(self.current_file_path, stat.S_IREAD)  # Set to read only
        os.rename(self.current_file_path, self.temp_file_path)  # Rename current save

        current_save_name = self.PC.GetPlayerUINamePreference()
        self.PC.SetPlayerUINamePreference(self.new_save_name)
        self.PC.SaveGame()  # Saves a new copy
        os.chmod(self.current_file_path, stat.S_IREAD)  # Set new file read only

        # Rename files
        unrealsdk.Log(self.new_file_path)
        os.rename(self.current_file_path, self.new_file_path)
        os.rename(self.temp_file_path, self.current_file_path)

        # Set name back to previous
        self.PC.SetPlayerUINamePreference(current_save_name)


    def get_game_state(self):
        """Gets the current state of the game for values that cannot be saved in the game save file."""
        state = {}
        # Buck up, anarchy, and free shots
        state['buckup_stacks'] = len(self.glitches.get_skill_stacks(['ShieldProbeBoost']))
        state['anarchy_stacks'] = self.glitches.get_anarchy_stacks()
        state['freeshot_stacks'] = len(self.glitches.get_skill_stacks(['Vladof Half Ammo']))

        # Weapons
        weapons = self.PC.GetPawnInventoryManager().GetEquippedWeapons()
        state['weapons_merged'] = []
        for weapon in weapons:
            if weapon:
                if len(weapon.ExternalAttributeModifiers) > 0:
                    state['weapons_merged'].append(weapon.QuickSelectSlot)
        state['active_weapon'] = self.PC.GetActiveOrBestWeapon().QuickSelectSlot

        # Position (using commander)
        state['position'] = _GetPosition(self.PC)
        return state

    def save_checkpoint(self):
        """Saves game and game state with the hash of the save file."""
        self.save_game_copy()
        state = self.get_game_state()
        unrealsdk.Log(state)

        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r") as f:
                existing = json.load(f)
        else:
            existing = {}

        # Set state data by hash value of the save file
        existing[Utilities.get_hash(self.new_file_path)] = state
        with open(_STATE_PATH, "w") as f:
            json.dump(existing, f)

    def get_game_state_from_state_file(self):
        """Retrieves game state from state.json based on the hash of the save file"""
        hash = Utilities.get_hash(self.current_file_path)
        with open(_STATE_PATH, "r") as f:
            states = json.load(f)
        if not states.get(hash):
            Utilities.feedback("No game state data found for this save file")
            return
        return states.get(hash)

    def load_game_state(self):
        """Loads the game state by applying glitches and the saved map position."""
        load_state = self.get_game_state_from_state_file()
        if not load_state:
            Utilities.feedback("No game state data found for this save file")
            return

        # Buck up, free shots, anarchy
        self.glitches.set_buckup_stacks(load_state['buckup_stacks'])
        self.glitches.set_anarchy_stacks(load_state['anarchy_stacks'])
        self.glitches.set_infinite_ammo_stacks(load_state['freeshot_stacks'])

        # Weapon merges
        weapons = self.PC.GetPawnInventoryManager().GetEquippedWeapons()
        merge_msg = ''
        prefix = '\t'
        for weapon in weapons:
            if weapon and weapon.QuickSelectSlot in load_state['weapons_merged']:
                weapon.ApplyAllExternalAttributeEffects()
                merge_msg = merge_msg + prefix + weapon.GetShortHumanReadableName()
                prefix = '\n\t'

        # Position (using commander)
        _ApplyPosition(self.PC, load_state['position'])

        Utilities.feedback(
            f"Game State Loaded" +
            f"\nBuck Up Stacks: {load_state['buckup_stacks']}" +
            f"\nAnarchy Stacks: {load_state['anarchy_stacks']}" +
            f"\nFree Shot Stacks: {load_state['freeshot_stacks']}" +
            f"\nWeapons Merged:" +
            f"\n{merge_msg}"
        )


class SaveNameInput(TextInputBox):
    """Input box class whose only responsibility is to set the message and call the saver class for handling"""

    def OnSubmit(self, Message: str) -> None:
        """Override base class method. This is called when the text box is closed."""
        if Message:
            checkpoint_saver = CheckpointSaver(Message)
            checkpoint_saver.save_checkpoint()


class AnyPercentHelper(ModMenu.SDKMod):
    Name: str = "Any% Helper"
    Author: str = "Justin99"
    Description: str = "Various utilities for practicing Any% Gaige speedruns on current patch"
    Version: str = "1.2.0"
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
    ]

    def GameInputPressed(self, input) -> None:
        """Handle methods that need the class instance here"""
        glitches = Glitches()

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
            glitches = Glitches()
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
        glitches = Glitches()
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
