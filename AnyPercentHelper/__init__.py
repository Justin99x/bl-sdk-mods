import hashlib
import inspect
import json
import os
from time import sleep
from typing import cast

import unrealsdk
from Mods.Commander import _ApplyPosition, _GetPosition
from Mods import ModMenu

from Mods.UserFeedback import TextInputBox

_FILEDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))


class Utilities:
    _DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")

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

    @classmethod
    def feedback(cls, feedback):
        """Presents a "training" message to the user with the given string"""
        PC = cls.get_current_player_controller()
        HUDMovie = PC.GetHUDMovie()
        if HUDMovie is None:
            return

        duration = 3.0 * cls._DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
        HUDMovie.ClearTrainingText()
        HUDMovie.AddTrainingText(feedback, "Gaige Any% Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                                 True)

    @staticmethod
    def get_hash(filepath):
        with open(filepath, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.new("sha256", file_contents).hexdigest()

        return file_hash


class Glitches:

    @staticmethod
    def _add_skill_definition_instance(skill_msg_name, template_obj_str):
        PC = Utilities.get_current_player_controller()
        skill_manager = PC.GetSkillManager()
        new_skill = Utilities.clone_obj(skill_msg_name, 'SkillDefinition', template_obj_str)

        skill_name = new_skill.SkillName
        old_stacks = len([skill.Definition for skill in skill_manager.ActiveSkills if
                          skill.Definition.SkillName == skill_name])
        skill_manager.ActivateSkill(PC, new_skill)
        new_stacks = len([skill.Definition for skill in skill_manager.ActiveSkills if
                          skill.Definition.SkillName == skill_name])

        Utilities.feedback(f"Changed {skill_msg_name} stacks from {old_stacks} to {new_stacks}")

    @staticmethod
    def _remove_skill_definition_instance(skill_msg_name, skill_name):
        PC = Utilities.get_current_player_controller()
        skill_manager = PC.GetSkillManager()

        skill_stacks = [skill.Definition for skill in skill_manager.ActiveSkills if
                        skill.Definition.SkillName == skill_name]
        old_stacks = len(skill_stacks)
        if skill_stacks:
            skill_manager.DeactivateSkill(PC, skill_stacks[0])
            Utilities.feedback(f"Changed {skill_msg_name} stacks from {old_stacks} to {old_stacks - 1}")
            return
        Utilities.feedback(f"No {skill_msg_name} stacks available to remove")

    @classmethod
    def add_buckup_stack(cls) -> None:
        cls._add_skill_definition_instance('Buck Up', 'GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player')

    @classmethod
    def remove_buckup_stack(cls) -> None:
        cls._remove_skill_definition_instance('Buck Up', 'ShieldProbeBoost')

    @classmethod
    def add_infinite_ammo_stack(cls) -> None:
        cls._add_skill_definition_instance('Vladof Free Shot', 'GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo')

    @classmethod
    def remove_infinite_ammo_stack(cls) -> None:
        cls._remove_skill_definition_instance('Vladoff Free Shot', 'Vladof Half Ammo')

    @staticmethod
    def add_anarchy_stacks() -> None:
        PC = Utilities.get_current_player_controller()
        anarchy_attr = unrealsdk.FindObject("DesignerAttributeDefinition",
                                            "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")
        max_stacks_attr = unrealsdk.FindObject("DesignerAttributeDefinition",
                                               "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_StackCap")
        max_stacks = max_stacks_attr.GetValue(PC)[0]
        current_stacks = anarchy_attr.GetValue(PC)[0]
        anarchy_attr.SetAttributeBaseValue(PC, min(current_stacks + 10, max_stacks))
        Utilities.feedback("Added 10 stacks of anarchy")

    @staticmethod
    def merge_all_equipped_weapons() -> None:
        PC = Utilities.get_current_player_controller()
        inv_manager = PC.GetPawnInventoryManager()
        weapons = inv_manager.GetEquippedWeapons()
        msg = ''
        for weapon in weapons:
            if weapon:
                weapon.ApplyAllExternalAttributeEffects()
                msg = msg + '\n' + weapon.GetShortHumanReadableName()
        Utilities.feedback(f"Bonuses from the following weapons are applied: {msg}")

    @staticmethod
    def handle_jakobs_auto(new_value):
        PC = Utilities.get_current_player_controller()
        autoburst_attr = unrealsdk.FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponAutomaticBurstCount")
        weapons = unrealsdk.FindAll('WillowWeapon')
        jakobs_shotguns = [weapon for weapon in weapons if
                           weapon.DefinitionData.WeaponTypeDefinition is not None and weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun']
        if new_value:
            PC.ConsoleCommand(
                f"set WeaponTypeDefinition'GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun' AutomaticBurstCount 0")
            for js in jakobs_shotguns:
                autoburst_attr.SetAttributeBaseValue(js, 0)
        else:
            PC.ConsoleCommand(
                f"set WeaponTypeDefinition'GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun' AutomaticBurstCount 1")
            for js in jakobs_shotguns:
                autoburst_attr.SetAttributeBaseValue(js, 1)


class CheckpointSaver(TextInputBox):
    def __init__(
            self,
            Title: str,
            DefaultMessage: str = "",
            PausesGame: bool = False,
            Priority: int = 254,
            save_dir: str = ""
    ) -> None:
        self.Title = Title
        self.DefaultMessage = DefaultMessage
        self.PausesGame = PausesGame
        self.Priority = Priority

        self._Message = list(DefaultMessage)
        self._CursorPos = 0
        self._IsShiftPressed = False
        self._TrainingBox = None

        self.save_dir = save_dir
        self.PC = Utilities.get_current_player_controller()
        self.state_path = self.get_state_path()

    def OnSubmit(self, Message: str) -> None:
        if Message == "":
            return

        PC = Utilities.get_current_player_controller()
        unrealsdk.Log(self.save_dir)
        current_file_path, new_file_path, temp_file_path = self.get_save_file_paths()

        os.chmod(current_file_path, 0o444)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        os.rename(current_file_path, temp_file_path)

        PC.SetPlayerUINamePreference(Message)
        PC.SaveGame()
        os.chmod(current_file_path, 0o444)  # New file read only for later practice
        self.save_game_state()

        os.rename(temp_file_path, new_file_path)

    @staticmethod
    def get_state_path():
        return os.path.join(os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None))), "state.json")

    def get_current_file_path(self):
        current_file_name = self.PC.GetWillowGlobals().GetWillowSaveGameManager().LastLoadedFilePath
        return os.path.join(self.save_dir, current_file_name)

    def get_save_file_paths(self):
        current_file_name = self.PC.GetWillowGlobals().GetWillowSaveGameManager().LastLoadedFilePath
        current_file_path = os.path.join(self.save_dir, current_file_name)

        if not (os.path.exists(current_file_path) and os.path.isfile(current_file_path)):
            Utilities.feedback("Error finding current filepath")
            return

        i = 0
        while True:
            i += 1
            try_new_file_name = f"Save{int(current_file_name[4:8]) + i}.sav"
            if not os.path.exists(os.path.join(self.save_dir, try_new_file_name)):
                new_file_name = try_new_file_name
                break

        new_file_path = os.path.join(self.save_dir, new_file_name)
        temp_file_path = os.path.join(self.save_dir, 'tempsav.sav')

        return current_file_path, new_file_path, temp_file_path

    def get_game_state(self):
        def _get_stack_num(skill_name):
            return len([skill.Definition for skill in skill_manager.ActiveSkills if
                        skill.Definition.SkillName == skill_name])

        skill_manager = self.PC.GetSkillManager()
        inv_manager = self.PC.GetPawnInventoryManager()

        state = {}
        # Buck up and free shots
        state['buckup_stacks'] = _get_stack_num('ShieldProbeBoost')
        state['free_shot_stacks'] = _get_stack_num('Vladof Half Ammo')

        # Anarchy stacks
        anarchy_attr = unrealsdk.FindObject("DesignerAttributeDefinition",
                                            "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")
        state['anarchy_stacks'] = anarchy_attr.GetValue(self.PC)[0]

        # Weapon merging
        weapons = inv_manager.GetEquippedWeapons()
        state['weapons_merged'] = []
        for weapon in weapons:
            if weapon:
                if len(weapon.ExternalAttributeModifiers) > 0:
                    state['weapons_merged'].append(weapon.QuickSelectSlot)

        # Active weapon
        state['active_weapon'] = self.PC.GetActiveOrBestWeapon().QuickSelectSlot

        # Position (using commander)
        state['position'] = _GetPosition(self.PC)
        return state

    def save_game_state(self):
        current_file_path = self.get_current_file_path()
        state = self.get_game_state()

        state_path = self.state_path
        if os.path.exists(state_path):
            with open(state_path, "r") as f:
                existing = json.load(f)
        else:
            existing = {}

        # Set state data by hash value of the save file
        existing[Utilities.get_hash(current_file_path)] = state
        with open(state_path, "w") as f:
            json.dump(existing, f)

    def load_game_state(self):
        PC = Utilities.get_current_player_controller()
        inv_manager = PC.GetPawnInventoryManager()
        current_file_path = self.get_current_file_path()
        hash = Utilities.get_hash(current_file_path)

        with open(self.state_path, "r") as f:
            states = json.load(f)
        if not states.get(hash):
            unrealsdk.Log(hash)
            Utilities.feedback("No game state data found for this save file")
            return
        state = states.get(hash)

        # Buck up and free shots
        for i in range(state['buckup_stacks']):
            Glitches.add_buckup_stack()
        for i in range(state['free_shot_stacks']):
            Glitches.add_infinite_ammo_stack()

        # Anarchy stacks
        anarchy_attr = unrealsdk.FindObject("DesignerAttributeDefinition",
                                            "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")
        anarchy_attr.SetAttributeBaseValue(PC, state['anarchy_stacks'])

        if state['active_weapon'] == PC.ActiveWeaponSlot:
            block_remove_attribute = False
        else:
            block_remove_attribute = True
            PC.EquipWeaponFromSlot(state['active_weapon'])

        # Reset swap values and apply crit bonuses
        weapons = inv_manager.GetEquippedWeapons()
        for weapon in weapons:
            if weapon:
                if weapon.QuickSelectSlot in state['weapons_merged']:
                    weapon.ApplyAllExternalAttributeEffects()

        # Position (using commander)
        _ApplyPosition(PC, state['position'])

        return block_remove_attribute

    def show_game_state(self):
        state = self.get_game_state()
        PC = Utilities.get_current_player_controller()
        crit_attr = unrealsdk.FindObject("AttributeDefinition",
                                         "D_Attributes.GameplayAttributes.PlayerCriticalHitBonus")
        crit = crit_attr.GetValue(PC)[0]

        msg = f"Buckup Stacks: {state['buckup_stacks']}"
        msg += f"\nFree Shot Stacks: {state['free_shot_stacks']}"
        msg += f"\nCritical Hit Bonus: {round(crit, 2)}"
        Utilities.feedback(msg)


class AnyPercentHelper(ModMenu.SDKMod):
    Name: str = "Any% Helper"
    Author: str = "Justin99"
    Description: str = "TBD"
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    Keybinds = [
        ModMenu.Keybind("Add Buckup Stack", "None", OnPress=Glitches.add_buckup_stack),
        ModMenu.Keybind("Remove Buckup Stack", "None", OnPress=Glitches.remove_buckup_stack),
        ModMenu.Keybind("Add 10 Anarchy Stacks", "None", OnPress=Glitches.add_anarchy_stacks),
        ModMenu.Keybind("Add Free Shot Stack", "None", OnPress=Glitches.add_infinite_ammo_stack),
        ModMenu.Keybind("Remove Free Shot Stack", "None", OnPress=Glitches.remove_infinite_ammo_stack),
        ModMenu.Keybind("Merge Equipped Weapons", "None", OnPress=Glitches.merge_all_equipped_weapons),
        ModMenu.Keybind("Save Checkpoint", "None"),
        ModMenu.Keybind("Load Checkpoint State", "None"),
        ModMenu.Keybind("Show Glitch State", "None"),
    ]

    def __init__(self):
        self.loading_checkpoint_state = False
        self.save_dir = self.get_save_dir_from_config(_FILEDIR)
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
        self.Options = [
            self.FullAmpDamageBoolean,
            self.WeaponMerging,
            self.VladofInfiniteAmmo,
            self.JakobsAutoFire
        ]

    def GameInputPressed(self, input) -> None:
        """Handle methods that need the class instance here"""
        if input.Name == "Save Checkpoint":
            self.save_checkpoint()
        if input.Name == "Load Checkpoint State":
            self.load_checkpoint_state()
        if input.Name == "Show Glitch State":
            self.show_glitch_state()

    def ModOptionChanged(self, option: ModMenu.Options.Base, new_value) -> None:
        """For anything that needs to be called on changing an option in the game menu"""
        if option == self.JakobsAutoFire:
            Glitches.handle_jakobs_auto(new_value)

    def save_checkpoint(self):
        """Saves the game and stores info about the game state of the player's glitches and position"""
        checkpoint_saver = CheckpointSaver("Character Save Name", PausesGame=True,
                                           save_dir=self.save_dir)
        checkpoint_saver.Show()

    def load_checkpoint_state(self):
        """Loads the game state of player glitches and position based on the hash of the save file last loaded"""
        checkpoint_saver = CheckpointSaver("Character Save Name", PausesGame=True,
                                           save_dir=self.save_dir)
        self.block_remove_attribute = checkpoint_saver.load_game_state()

    def show_glitch_state(self):
        """Shows buckup stacks, infinite ammo stacks, and critical hit bonus"""
        checkpoint_saver = CheckpointSaver("Character Save Name", PausesGame=True,
                                           save_dir=self.save_dir)
        checkpoint_saver.show_game_state()

    def get_save_dir_from_config(self, config_dir):
        config_path = os.path.join(config_dir, "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        return config["LocalGameSaves"]

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
        """
        Adjust damage bonus any time the skill is resumed.
        """
        if caller.Definition.Name not in ['Impact_Shield_Skill_Legendary', 'Impact_Shield_Skill']:
            return True
        PC = Utilities.get_current_player_controller()
        active_weapon = PC.GetActiveOrBestWeapon()
        self._apply_full_amp(active_weapon, caller)
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.OnEquip')
    def amp_on_equip(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                     params: unrealsdk.FStruct) -> bool:
        """
        Adjust damage bonus when swapping to a new weapon with full shield
        since it may have a different projectile count.
        """
        PC = Utilities.get_current_player_controller()
        if caller != PC.GetActiveOrBestWeapon():
            return True
        skill_manager = PC.GetSkillManager()
        impact_skill_names = ['Impact_Shield_Skill_Legendary', 'Impact_Shield_Skill']

        # Get impact shield skills. Sometimes there can be paused skills that never go away, so we only
        # want to apply to active skills. The Skill.Resume() hook will cover any we missed.
        impact_shield_skills = [skill for skill in skill_manager.ActiveSkills if
                                skill.Definition.Name in impact_skill_names]
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
        if self.block_remove_attribute:
            return False
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.OnEquip')
    def set_block_remove_attribute(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                   params: unrealsdk.FStruct) -> bool:
        """Handling of flag for blocking removal of attribute effects. Needed for loading checkpoint"""
        self.block_remove_attribute = False
        return True

    """
    Next 3 hooks are all to replicate infinite ammo glitch from Vladof launcher. Don't have enough information in
    just the deactivate skill hook to tell whether to block it or not. We're looking for whether we just equipped or
    just dropped the weapon, in which case we block the deactivation.
    """

    @ModMenu.Hook('WillowGame.WillowInventoryManager.RemoveFromInventory')
    def set_dropped_vladof_flag(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                params: unrealsdk.FStruct) -> bool:

        if params.ItemToRemove.Class == 'WillowWeapon' and params.ItemToRemove.DefinitionData.WeaponTypeDefinition.Name == 'WT_Vladof_Launcher':
            self.block_deactivate_half_ammo = True
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.OnEquip')
    def set_equipped_vladof_flag(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                 params: unrealsdk.FStruct) -> bool:
        if caller.DefinitionData.WeaponTypeDefinition.Name == 'WT_Vladof_Launcher':
            self.block_deactivate_half_ammo = True
        return True

    @ModMenu.Hook('WillowGame.SkillEffectManager.DeactivateSkill')
    def block_deactivate_free_shot(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                   params: unrealsdk.FStruct) -> bool:
        """
        Block when the flag is set and reset the flag.
        """
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
