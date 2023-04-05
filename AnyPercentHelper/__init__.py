import unrealsdk
from Mods import ModMenu
from Mods.EridiumLib import getCurrentPlayerController

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")

barrel_projectiles = {
    'SG_Barrel_Jakobs': 6,
    'SG_Barrel_Bandit': 8,
    'SG_Barrel_Hyperion': 0,
    'SG_Barrel_Tediore': 0,
    'SG_Barrel_Torgue': 11
}
accessory_projectiles = {
    'SG_Accessory_VerticalGrip': 2
}


def _clone_obj(new_name, in_class_str, template_obj_str):
    obj_to_clone = unrealsdk.FindObject(in_class_str, template_obj_str)
    return unrealsdk.ConstructObject(Class=in_class_str, Outer=obj_to_clone.Outer, Name=new_name, Template=obj_to_clone)


def _Feedback(feedback):
    """Presents a "training" message to the user with the given string."""
    PC = getCurrentPlayerController()
    HUDMovie = PC.GetHUDMovie()
    if HUDMovie is None:
        return

    duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
    HUDMovie.ClearTrainingText()
    HUDMovie.AddTrainingText(feedback, "Gaige Any% Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                             True)


def _add_skill_definition_instance(skill_msg_name, template_obj_str):
    PC = getCurrentPlayerController()
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
    PC = getCurrentPlayerController()
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


def do_10_fake_reloads() -> None:
    PC = getCurrentPlayerController()
    skill_manager = PC.GetSkillManager()
    skill_manager.NotifySkillDamagedEvent(4, PC, PC, None)
    for i in range(10):
        skill_manager.NotifySkillEvent(21, PC, PC)


def merge_all_equipped_weapons() -> None:
    PC = getCurrentPlayerController()
    inv_manager = PC.GetPawnInventoryManager()
    weapons = inv_manager.GetEquippedWeapons()
    msg = ''
    for weapon in weapons:
        if weapon:
            weapon.ApplyAllExternalAttributeEffects()
            msg = msg + '\n' + (weapon.DefinitionData.PrefixPartDefinition.PartName + ' ' or '') + weapon.DefinitionData.TitlePartDefinition.PartName
    _Feedback(f"Bonuses from the following weapons are applied: {msg}")

class AnyPercentHelper(ModMenu.SDKMod):
    Name: str = "Any% Helper"
    Author: str = "Justin99"
    Description: str = "TBD"
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings
    Keybinds = [
        ModMenu.Keybind("Add Buckup Stack", "None", OnPress=add_buckup_stack),
        ModMenu.Keybind("Remove Buckup Stack", "None", OnPress=remove_buckup_stack),
        ModMenu.Keybind("Add Anarchy Stacks", "None", OnPress=do_10_fake_reloads),
        ModMenu.Keybind("Merge Equipped Weapons", "None", OnPress=merge_all_equipped_weapons),
        ModMenu.Keybind("Add Free Shot Stack", "None", OnPress=add_infinite_ammo_stack),
        ModMenu.Keybind("Remove Free Shot Stack", "None", OnPress=remove_infinite_ammo_stack),
    ]

    def __init__(self):
        """
        This is for the Vladof infinite ammo glitch. Don't need to call super since SDKMod uses __new__
        """
        self.block_deactivate_half_ammo = False

    def _apply_full_amp(self, active_weapon, impact_shield_skill):
        """
        Apply full amp damage to every pellet. Assumes the skill is already active or about to be resumed. We get the
        base damage of the weapon with no skill applied, then the damage with the skill applied. Compare that difference
        to the expected total amp damage and we get our pellet estimate. We replace the skill scale constant with the
        projectile count to effectively give every pellet full amp damage.
        """
        impact_shield_skill.Deactivate()
        weapon_damage_base = active_weapon.GetMultiProjectileDamage()

        impact_shield_skill.Activate()
        weapon_damage_impact_base = active_weapon.GetMultiProjectileDamage()

        weapon_damage_effect = [effect for effect in impact_shield_skill.SkillEffects if
                                effect.EffectData.AttributeToModify.Name == "WeaponDamage"][0]
        if weapon_damage_base >= weapon_damage_impact_base:
            projectiles = 1  # Just reset scale value to default. It will get modified again when skill resumed.
        else:
            impact_damage_full = weapon_damage_effect.Modifier.Value
            impact_damage_split = weapon_damage_impact_base - weapon_damage_base
            projectiles = round(impact_damage_full / impact_damage_split)
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
        PC = getCurrentPlayerController()
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
        PC = getCurrentPlayerController()
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
        PC = getCurrentPlayerController()
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
