from Mods.AnyPercentHelper.utilities import Utilities

import unrealsdk


class GlitchManager:
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