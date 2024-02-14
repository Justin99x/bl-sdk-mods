from typing import List

from Mods.SpeedrunPractice.utilities import Utilities
from Mods.UserFeedback import TextInputBox

from unrealsdk import FindObject, FindAll, Log, UObject


class GlitchManager:
    """Class for applying stacks (buck up, anarchy, etc.) arbitrarily"""

    def __init__(self):
        self.PC = Utilities.get_current_player_controller()
        self.skill_manager = self.PC.GetSkillManager()
        self.inventory_manager = self.PC.GetPawnInventoryManager()
        self.anarchy_attribute_def = FindObject("DesignerAttributeDefinition",
                                                "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")
        self.anarchy_max_stacks_attribute_def = FindObject("DesignerAttributeDefinition",
                                                           "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_StackCap")
        self.autoburst_attribute_def = FindObject("AttributeDefinition",
                                                  "D_Attributes.Weapon.WeaponAutomaticBurstCount")
        self.crititical_hit_bonus_attribute_def = FindObject("AttributeDefinition",
                                                             "D_Attributes.GameplayAttributes.PlayerCriticalHitBonus")

    def get_skill_stacks(self, skill_names: list) -> List:
        """Get SkillDefinition objects for active skills matching the name"""
        return [skill.Definition for skill in self.skill_manager.ActiveSkills if
                skill.Definition.Name in skill_names]

    def add_skill_definition_instance(self, skill_path_name) -> None:
        """Create new activated instance of skill definition"""
        skill_def = FindObject('SkillDefinition', skill_path_name)
        old_stacks = len(self.get_skill_stacks([skill_path_name.split('.')[-1]]))
        self.skill_manager.ActivateSkill(self.PC, skill_def)

    def remove_skill_definition_instance(self, skill_path_name) -> None:
        """Remove one instance of skill definition"""
        skill_stacks = self.get_skill_stacks([skill_path_name.split('.')[-1]])
        old_stacks = len(skill_stacks)
        if skill_stacks:
            self.skill_manager.DeactivateSkill(self.PC, skill_stacks[0])
            return

    def set_skill_stacks(self, target_stacks, skill_path_name) -> None:
        """Set stacks of skill to desired value"""
        current_stacks = len(self.get_skill_stacks([skill_path_name.split('.')[-1]]))
        for i in range(current_stacks):
            self.remove_skill_definition_instance(skill_path_name)
        for i in range(target_stacks):
            self.add_skill_definition_instance(skill_path_name)
        Log(f"Set {skill_path_name.split('.')[-1]} stacks to {target_stacks}")

    def get_anarchy_stacks(self) -> int:
        """Get stacks of anarchy from the attribute definition"""
        return int(self.anarchy_attribute_def.GetValue(self.PC)[0])

    def set_anarchy_stacks(self, target_stacks, dummy: str=None) -> None:
        """Set anarchy stacks to desired value. Dummy signature used to match text input handler"""
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

    def handle_jakobs_auto(self, new_value: bool) -> None:
        """Turns automatic Jakobs shotguns on or off. Used to mimic functionality of free scroll macro."""
        weapons = FindAll('WillowWeapon')
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

    def show_state(self) -> None:
        """Show current status of key values"""
        msg = f"Buckup Stacks: {len(self.get_skill_stacks(['Skill_ShieldBoost_Player']))}"
        msg += f"\nFree Shot Stacks: {len(self.get_skill_stacks(['Skill_VladofHalfAmmo']))}"
        msg += f"\nSmasher Chance Stacks: {len(self.get_skill_stacks(['Skill_EvilSmasher']))}"
        msg += f"\nSmasher SMASH Stacks: {len(self.get_skill_stacks(['Skill_EvilSmasher_SMASH']))}"
        msg += f"\nCritical Hit Bonus: {round(self.crititical_hit_bonus_attribute_def.GetValue(self.PC)[0], 2)}"
        Utilities.feedback(msg)
