from typing import cast

import unrealsdk
from unrealsdk import Log
from Mods import ModMenu

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")


def _get_current_player_controller() -> unrealsdk.UObject:
    """Returns the local player"""
    return cast(unrealsdk.UObject, unrealsdk.GetEngine().GamePlayers[0].Actor)


def _clone_obj(new_name, in_class_str, template_obj_str):
    """Creates a fresh object based on the class name and a template object defintion"""
    obj_to_clone = unrealsdk.FindObject(in_class_str, template_obj_str)
    return unrealsdk.ConstructObject(Class=in_class_str, Outer=obj_to_clone.Outer, Name=new_name, Template=obj_to_clone)


def _Feedback(feedback):
    """Presents a "training" message to the user with the given string"""
    PC = _get_current_player_controller()
    HUDMovie = PC.GetHUDMovie()
    if HUDMovie is None:
        return

    duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
    HUDMovie.ClearTrainingText()
    HUDMovie.AddTrainingText(feedback, "Gaige Any% Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                             True)


def _add_skill_definition_instance(skill_msg_name, template_obj_str):
    PC = _get_current_player_controller()
    skill_manager = PC.GetSkillManager()
    new_skill = _clone_obj(skill_msg_name, 'SkillDefinition', template_obj_str)

    skill_name = new_skill.SkillName
    old_stacks = len([skill.Definition for skill in skill_manager.ActiveSkills if
                      skill.Definition.SkillName == skill_name])
    skill_manager.ActivateSkill(PC, new_skill)
    new_stacks = len([skill.Definition for skill in skill_manager.ActiveSkills if
                      skill.Definition.SkillName == skill_name])

    _Feedback(f"Changed {skill_msg_name} stacks from {old_stacks} to {new_stacks}")


def _remove_skill_definition_instance(skill_msg_name, skill_name):
    PC = _get_current_player_controller()
    skill_manager = PC.GetSkillManager()

    skill_stacks = [skill.Definition for skill in skill_manager.ActiveSkills if
                    skill.Definition.SkillName == skill_name]
    old_stacks = len(skill_stacks)
    if skill_stacks:
        skill_manager.DeactivateSkill(PC, skill_stacks[0])
        _Feedback(f"Changed {skill_msg_name} stacks from {old_stacks} to {old_stacks - 1}")
        return
    _Feedback(f"No {skill_msg_name} stacks available to remove")


def add_buckup_stack() -> None:
    _add_skill_definition_instance('Buck Up', 'GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player')


def remove_buckup_stack() -> None:
    _remove_skill_definition_instance('Buck Up', 'ShieldProbeBoost')


def add_infinite_ammo_stack() -> None:
    _add_skill_definition_instance('Vladof Free Shot', 'GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo')


def remove_infinite_ammo_stack() -> None:
    _remove_skill_definition_instance('Vladoff Free Shot', 'Vladof Half Ammo')


def add_anarchy_stacks() -> None:
    PC = _get_current_player_controller()
    anarchy_attr = unrealsdk.FindObject("DesignerAttributeDefinition",
                                        "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")
    max_stacks_attr = unrealsdk.FindObject("DesignerAttributeDefinition",
                                           "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_StackCap")
    max_stacks = max_stacks_attr.GetValue(PC)[0]
    current_stacks = anarchy_attr.GetValue(PC)[0]
    anarchy_attr.SetAttributeBaseValue(PC, min(current_stacks + 10, max_stacks))
    _Feedback("Added 10 stacks of anarchy")


def merge_all_equipped_weapons() -> None:
    PC = _get_current_player_controller()
    inv_manager = PC.GetPawnInventoryManager()
    weapons = inv_manager.GetEquippedWeapons()
    msg = ''
    for weapon in weapons:
        if weapon:
            weapon.ApplyAllExternalAttributeEffects()
            msg = msg + '\n' + weapon.GetShortHumanReadableName()
    _Feedback(f"Bonuses from the following weapons are applied: {msg}")


class AnyPercentHelper(ModMenu.SDKMod):
    Name: str = "Any% Helper"
    Author: str = "Justin99"
    Description: str = "Various utilities for practicing Any% speedruns on current patch"
    Version: str = "1.0.1"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings
    Keybinds = [
        ModMenu.Keybind("Add Buckup Stack", "None", OnPress=add_buckup_stack),
        ModMenu.Keybind("Remove Buckup Stack", "None", OnPress=remove_buckup_stack),
        ModMenu.Keybind("Add 10 Anarchy Stacks", "None", OnPress=add_anarchy_stacks),
        ModMenu.Keybind("Merge Equipped Weapons", "None", OnPress=merge_all_equipped_weapons),
        ModMenu.Keybind("Add Free Shot Stack", "None", OnPress=add_infinite_ammo_stack),
        ModMenu.Keybind("Remove Free Shot Stack", "None", OnPress=remove_infinite_ammo_stack),
    ]

    def __init__(self):
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
        self.Options = [
            self.FullAmpDamageBoolean,
            self.WeaponMerging,
            self.VladofInfiniteAmmo
        ]

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
        PC = _get_current_player_controller()
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
        PC = _get_current_player_controller()
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
        PC = _get_current_player_controller()
        inv_manager = PC.GetPawnInventoryManager()

        if PC.bStatusMenuOpen and inv_manager.PendingWeapon:
            return False
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
