from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable, List, TYPE_CHECKING, cast

import Mods.BorderlandsRewind as BLR
from Mods.BorderlandsRewind.utilities import feedback, get_pc, is_client, text_input_stacks
from Mods.ModMenu import Keybind
from unrealsdk import ConstructObject, FindAll, FindObject, Log

if TYPE_CHECKING:
    from bl2 import Skill, SkillDefinition, WillowPlayerController

KILL_NAME = 'kill skill'


def merge_equipped_weapons() -> None:
    """Applies external attribute effects from all weapons currently equipped. Used for crit bonus in runs."""
    weapons = get_pc().GetPawnInventoryManager().GetEquippedWeapons()
    msg = ''
    for weapon in weapons:
        if weapon:
            weapon.ApplyAllExternalAttributeEffects()
            msg = msg + '\n' + weapon.GetShortHumanReadableName()
    feedback(f"Bonuses from the following weapons are applied: {msg}")


def local_set_skill_stacks(skill_def_path: str, target_stacks: int, target_pc: WillowPlayerController):
    pc = get_pc()
    in_skill_def: SkillDefinition | None = FindObject('SkillDefinition', skill_def_path)

    for skill in pc.GetSkillManager().ActiveSkills:
        if not skill.SkillInstigator == target_pc:
            continue
        if skill.Definition == in_skill_def or (skill_def_path == KILL_NAME and skill.Definition.SkillType == 3):
            skill.Deactivate()

    kill_skill_defs = [skill.Definition for skill in pc.PlayerSkillTree.Skills if
                       skill.Definition.SkillType == 3 and skill_def_path == KILL_NAME]  # type: ignore

    for skill_def in kill_skill_defs + [in_skill_def]:
        for i in range(target_stacks):
            pc.GetSkillManager().ActivateSkill(target_pc, skill_def, None, pc.GetSkillGrade(skill_def))


def set_skill_stacks(skill_def_path: str, target_stacks: int) -> None:
    if not is_client():
        local_set_skill_stacks(skill_def_path, target_stacks, get_pc())
        feedback(f"Set {skill_def_path.split('.')[-1]} stacks to {target_stacks}")
    else:
        BLR.instance.server_set_skill_stacks(skill_def_path, target_stacks)


def set_free_shot_stacks():
    text_input_stacks(set_skill_stacks, "Set Free Shot Stacks", "GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo")


def set_smasher_chance_stacks():
    text_input_stacks(set_skill_stacks, "Set Smasher Chance Stacks", "GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher_SMASH")


def set_buckup_stacks():
    text_input_stacks(set_skill_stacks, "Set Buckup Stacks", "GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player")


def set_maya_gaige_kill_stacks():
    PC = get_pc()
    if PC.PlayerClass.Name in ['CharClass_Mechromancer', 'CharClass_Siren']:
        text_input_stacks(set_skill_stacks, "Set Kill Skill Stacks", KILL_NAME)
    else:
        feedback("Only available for Maya or Gaige")


def set_expertise_stacks():
    PC = get_pc()
    if PC.PlayerClass.Name == 'CharClass_Soldier':
        text_input_stacks(set_skill_stacks, "Set Expertise Stacks", "GD_Soldier_Skills.Gunpowder.Expertise_MovementSpeed")
    else:
        feedback("Only available for Axton")


buckup = Keybind("Set Buckup Stacks", "None", OnPress=set_buckup_stacks)
free_shot = Keybind("Set Free Shot Stacks", "None", OnPress=set_free_shot_stacks)
smasher = Keybind("Set Smasher Chance Stacks", "None", OnPress=set_smasher_chance_stacks)
kill_skills = Keybind("Set Kill Skill Stacks", "None", OnPress=set_maya_gaige_kill_stacks)
expertise = Keybind("Set Expertise Stacks", "None", OnPress=set_expertise_stacks)
merge_weapons = Keybind("Merge Equipped Weapons", "None", OnPress=merge_equipped_weapons)

blr_keybinds = [buckup, free_shot, smasher, kill_skills, expertise, merge_weapons]
