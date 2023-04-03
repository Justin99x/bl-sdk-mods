import unrealsdk
from Mods import ModMenu
from Mods.EridiumLib import getCurrentPlayerController

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")

barrel_projectiles =  {
    'SG_Barrel_Jakobs': 6,
    'SG_Barrel_Bandit': 8,
    'SG_Barrel_Hyperion': 0,
    'SG_Barrel_Tediore': 0,
    'SG_Barrel_Torgue': 11
}
accessory_projectiles = {
    'SG_Accessory_VerticalGrip': 2
}

def _Feedback(feedback):
    """Presents a "training" message to the user with the given string."""
    PC = getCurrentPlayerController()
    HUDMovie = PC.GetHUDMovie()
    if HUDMovie is None:
        return

    duration = 2.0 * _DefaultGameInfo.GameSpeed # We will be displaying the message for two *real time* seconds.
    HUDMovie.ClearTrainingText()
    HUDMovie.AddTrainingText(feedback, "Gaige Any% Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo, True)

def do_10_fake_reloads() -> None:
    PC = getCurrentPlayerController()
    skill_manager = PC.GetSkillManager()
    skill_manager.NotifySkillDamagedEvent(4, PC, PC, None)
    for i in range(10):
        skill_manager.NotifySkillEvent(21, PC, PC)

def add_buckup_stack() -> None:
    PC = getCurrentPlayerController()
    cloned_obj = unrealsdk.FindObject('SkillDefinition', 'GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player')
    new_object = unrealsdk.ConstructObject(Class='SkillDefinition', Outer=cloned_obj.Outer, Name='NewShieldBoost', Template=cloned_obj)

    skill_manager = PC.GetSkillManager()
    skill_name = 'ShieldProbeBoost'
    old_stacks = len([skill.Definition for skill in skill_manager.ActiveSkills if
                     skill.Definition.SkillName == skill_name])
    skill_manager.ActivateSkill(PC, new_object)
    new_stacks = len([skill.Definition for skill in skill_manager.ActiveSkills if
                       skill.Definition.SkillName == skill_name])
    _Feedback(f"Changed Buckup stacks from {old_stacks} to {new_stacks}")

def remove_buckup_stack() -> None:
    PC = getCurrentPlayerController()
    skill_manager = PC.GetSkillManager()
    skill_name = 'ShieldProbeBoost'

    shield_boosts = [skill.Definition for skill in skill_manager.ActiveSkills if skill.Definition.SkillName == skill_name]
    old_stacks = len(shield_boosts)
    if shield_boosts:
        skill_manager.DeactivateSkill(PC, shield_boosts[0])
        _Feedback(f"Changed Buckup stacks from {old_stacks} to {old_stacks-1}")
        return
    _Feedback(f"No Buckup stacks available to remove")


class AnyPercentHelper(ModMenu.SDKMod):
    Name: str = "Any% Helper"
    Author: str = "Justin99"
    Description: str = "TBD"
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings
    Keybinds = [
        ModMenu.Keybind("Add Buckup Stack", "F1", OnPress=add_buckup_stack),
        ModMenu.Keybind("Remove Buckup Stack", "F2", OnPress=remove_buckup_stack),
        ModMenu.Keybind("Add Anarchy Stacks", "F3", OnPress=do_10_fake_reloads)
    ]

    def __init__(self):
        """
        This is for the Vladof infinite ammo glitch. Don't need to call super since SDKMod uses __new__
        """
        self.block_deactivate_half_ammo = False

    @ModMenu.Hook('WillowGame.Skill.AdjustModifiers')
    def amp_damage(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                                           params: unrealsdk.FStruct) -> bool:
        """
        Hacky solution to mimic full amp damage spread across all pellets.
        """
        if caller.Definition.Name in ('Impact_Shield_Skill', 'Impact_Shield_Skill_Legendary'):
            skill_effs = caller.SkillEffects
            for skill_eff in skill_effs:
                if skill_eff.EffectData.AttributeToModify.Name == "WeaponDamage":
                    weapons = skill_eff.Contexts
                    for weapon in weapons:
                        if weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun':
                            base_projectiles = 7
                            from_barrel = barrel_projectiles.get(weapon.DefinitionData.BarrelPartDefinition.Name, 0)
                            from_vertical_grip = accessory_projectiles.get(
                                weapon.DefinitionData.Accessory1PartDefinition.Name, 0)
                            final_projectiles = base_projectiles + from_barrel + from_vertical_grip
                            skill_eff.EffectData.BaseModifierValue.BaseValueScaleConstant = final_projectiles
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.RemoveAllExternalAttributeEffects')
    def allow_weapon_merging(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Allow merging weapons to keep crit bonuses, healing, etc.
        """
        PC = getCurrentPlayerController()
        inv_manager = PC.GetPawnInventoryManager()

        if PC.bStatusMenuOpen and inv_manager.PendingWeapon:
            return False
        return True

    """
    Next few hooks are all to replicate infinite ammo glitch from Vladof launcher. Don't have enough information in
    just the deactivate skill hook to tell whether to block it or not. We're looking for whether we just equipped or
    just dropped the weapon, in which case we block the deactivation.
    """
    @ModMenu.Hook('WillowGame.WillowInventoryManager.RemoveFromInventory')
    def set_dropped_vladof_flag(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
               params: unrealsdk.FStruct) -> bool:
        unrealsdk.Log(f'{caller} Called WillowGame.WillowInventoryManager.RemoveFromInventory')
        unrealsdk.Log(params)
        if params.ItemToRemove.DefinitionData.WeaponTypeDefinition.Name == 'WT_Vladof_Launcher':
            self.block_deactivate_half_ammo = True
        return True

    @ModMenu.Hook('WillowGame.WillowWeapon.OnEquip')
    def set_equipped_vladof_flag(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction,
               params: unrealsdk.FStruct) -> bool:
        unrealsdk.Log(f'{caller} Called WillowGame.WillowWeapon.OnEquip')
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
        unrealsdk.Log("I ARISE!")

    def Disable(self) -> None:
        unrealsdk.Log("I sleep.")
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