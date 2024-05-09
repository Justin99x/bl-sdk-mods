from typing import Callable, List

from Mods.SpeedrunPractice.utilities import get_current_player_controller, try_parse_int
from Mods.UserFeedback import TextInputBox
from unrealsdk import FindObject, Log, UObject


def get_skill_stacks(PC, skill_names: list) -> List:
    """Get SkillDefinition objects for active skills matching the name"""
    skill_manager = PC.GetSkillManager()
    return [skill.Definition for skill in skill_manager.ActiveSkills if
            skill.Definition.Name in skill_names]


def add_skill_definition_instance(PC, skill_path_name) -> None:
    """Create new activated instance of skill definition"""
    skill_def = FindObject('SkillDefinition', skill_path_name)
    PC.GetSkillManager().ActivateSkill(PC, skill_def)


def remove_skill_definition_instance(PC, skill_path_name) -> None:
    """Remove one instance of skill definition"""
    skill_stacks = get_skill_stacks(PC, [skill_path_name.split('.')[-1]])
    if skill_stacks:
        PC.GetSkillManager().DeactivateSkill(PC, skill_stacks[0])
        return


def set_skill_stacks(PC: UObject, target_stacks: int, skill_path_name: str) -> None:
    """Set stacks of skill to desired value"""
    current_stacks = len(get_skill_stacks(PC, [skill_path_name.split('.')[-1]]))
    for i in range(current_stacks):
        remove_skill_definition_instance(PC, skill_path_name)
    for i in range(target_stacks):
        add_skill_definition_instance(PC, skill_path_name)
    Log(f"Set {skill_path_name.split('.')[-1]} stacks to {target_stacks}")


def get_attribute_value(PC, attr_str):
    attribute_def = FindObject("AttributeDefinition", attr_str)
    return attribute_def.GetValue(PC)[0]


def get_designer_attribute_value(PC, designer_attr_str):
    attribute_def = FindObject("DesignerAttributeDefinition", designer_attr_str)
    return attribute_def.GetValue(PC)[0]

def set_designer_attribute_value(PC: UObject, target_value: int, designer_attr_str: str):
    attribute_def = FindObject("DesignerAttributeDefinition", designer_attr_str)
    attribute_def.SetAttributeBaseValue(PC, target_value)


def activate_skill(PC, skill_def_str: str) -> None:
    skill_def = FindObject('SkillDefinition', skill_def_str)
    PC.Behavior_ActivateSkill(skill_def)

def trigger_kill_skills(PC):
    PC.NotifyInstinctSkillAction(2)


def text_input_stacks(func: Callable[[UObject, int, str], None], title: str, ref: str = '') -> None:
    """Handle input box creation for various actions"""
    input_box = TextInputBox(title, PausesGame=True)
    PC = get_current_player_controller()

    def OnSubmit(msg: str) -> None:
        if msg:
            target_val = try_parse_int(msg)
            if target_val >= 0:
                func(PC, target_val, ref)
            else:
                Log("Value must be greater than 0")

    input_box.OnSubmit = OnSubmit
    input_box.Show()

