from __future__ import annotations

from typing import Callable, TYPE_CHECKING, cast

from Mods import ModMenu
import Mods.BorderlandsRewind as BLR
from Mods.BorderlandsRewind.utilities import get_pc, is_client

from unrealsdk import FStruct, FindObject, Log, RemoveHook, RunHook, UFunction, UObject

if TYPE_CHECKING:
    from bl2 import WillowPlayerController

def handle_skill_stacking_option(on: bool):

    if on:
        RunHook("Engine.Actor.TriggerGlobalEventClass", 'BLR Skill Stacking', allow_skill_stacking)
        RunHook('WillowGame.WillowInventoryManager.RemoveFromInventory', 'BLR Drop Stacking', allow_drop_stacking)

        get_pc().ConsoleCommand(f"set Behavior_ActivateSkill bNoSkillStacking False")
    else:
        RemoveHook("Engine.Actor.TriggerGlobalEventClass", 'BLR Skill Stacking')
        RemoveHook('WillowGame.WillowInventoryManager.RemoveFromInventory', 'BLR Drop Stacking')
        # No way to do ConsoleCommand to reset this since it's by object, will just have to wait until next game load in.

def handle_weapon_merge_option(on: bool):
    if on:
        RunHook("WillowGame.WillowPlayerController.ModalGameMenuOpening", "BLR Merge", allow_weapon_merge)
    else:
        RemoveHook("WillowGame.WillowPlayerController.ModalGameMenuOpening", "BLR Merge")

def handle_amp_option(on: bool):
    if on:
        RunHook('WillowGame.Skill.Resume', 'BLR Amp', amp_hook)
        RunHook('WillowGame.WillowWeapon.OnEquip', 'BLR Amp', amp_hook)

        handle_amp(True)
    else:
        RemoveHook('WillowGame.Skill.Resume', 'BLR Amp')
        RemoveHook('WillowGame.WillowWeapon.OnEquip', 'BLR Amp')

        handle_amp(False)

def allow_skill_stacking(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """Mimic version 1.1 and 1.3.1 behavior on bulk pickup radius and skill stacking. These reset on level load so no need to disable"""
    if params.InEventClass.Name == 'WillowSeqEvent_PlayerJoined':
        PC = get_pc()
        PC.ConsoleCommand(f"set Behavior_ActivateSkill bNoSkillStacking False")
    return True

def allow_drop_stacking(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """Allow dropping weapons to keep skill stacks. This follows the exact logic that made
    the glitch possible in the first place. They later added the OnUnequip call to the
    RemoveFromInventory method to fix it, so we're just blocking it."""

    def block_onunequip(caller: UObject, function: UFunction, params: FStruct) -> bool:
        return False

    RunHook('WillowGame.WillowWeapon.OnUnequip', 'SpeedrunPractice', block_onunequip)
    # DoInjectedCallNext()
    caller.RemoveFromInventory(params.ItemToRemove, params.bCanDrop)
    RemoveHook('WillowGame.WillowWeapon.OnUnequip', 'SpeedrunPractice')
    return False



def allow_weapon_merge(caller: WillowPlayerController, function: UFunction, params: FStruct) -> bool:
    """Allow merging weapons to keep crit bonuses, healing, etc. This follows the exact logic that made
    the glitch possible in the first place. They later added the ForcePutDownInactiveWeapon call to the
    ModalGameMenuOpening method to fix it, so we're just blocking it."""

    def block_putdown(caller: UObject, function: UFunction, params: FStruct) -> bool:
        Log("Blocked!")
        return False

    RunHook('WillowGame.WillowWeapon.ForcePutDownInactiveWeapon', 'BLR', block_putdown)
    caller.ModalGameMenuOpening()
    RemoveHook('WillowGame.WillowWeapon.ForcePutDownInactiveWeapon', 'BLR')
    return False


def amp_hook(caller: UObject, function: UFunction, params: FStruct):
    handle_amp(True)
    return True

def handle_amp(enabled: bool) -> None:
    if not is_client():
        local_handle_amp(enabled, get_pc())
    else:
        BLR.instance.server_handle_amp(enabled)


def local_handle_amp(enabled: bool, target_pc: WillowPlayerController) -> None:
    """
    Apply full amp damage to every pellet. We replace the skill scale constant with the
    projectile count to effectively give every pellet full amp damage.
    """
    pc = get_pc()
    try:
        active_weapon = target_pc.Pawn.Weapon
    except AttributeError:
        return
    if not active_weapon:
        return

    projectiles_attr = cast("AttributeDefinition", FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponProjectilesPerShot"))
    projectiles = projectiles_attr.GetValue(active_weapon)[0]

    amp_skills = [skill for skill in pc.GetSkillManager().ActiveSkills if
                  skill.Definition.Name in ['Impact_Shield_Skill_Legendary', 'Impact_Shield_Skill'] and skill.SkillInstigator == target_pc]
    for amp_skill in amp_skills:
        if amp_skill.SkillState == 1:
            weapon_damage_effect = [effect for effect in amp_skill.SkillEffects if
                                    effect.EffectData.AttributeToModify.Name == "WeaponDamage"][0]
            if enabled:
                weapon_damage_effect.EffectData.BaseModifierValue.BaseValueScaleConstant = projectiles
            else:
                weapon_damage_effect.EffectData.BaseModifierValue.BaseValueScaleConstant = 1

class BLROption(ModMenu.Options.Boolean):
    on_change: Callable[[bool], None]

    def __init__(self, *args, on_change, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_change = on_change


full_amp_option = BLROption(
    Caption="Full Amp Damage",
    Description="Applies full amp damage to all projectiles",
    StartingValue=False,
    Choices=("Off", "On"),
    on_change=handle_amp_option
)

weapon_merging_option = BLROption(
    Caption="Weapon Merging",
    Description="Allows weapon merging and drop stacking",
    StartingValue=False,
    Choices=("Off", "On"),
    on_change=handle_weapon_merge_option
)

skill_stacking_option = BLROption(
    Caption="Skill Stacking",
    Description="Allows weapon skill stacking such as Vladof free shots and Evil Smasher SMASH stacks",
    StartingValue=False,
    Choices=("Off", "On"),
    on_change=handle_skill_stacking_option
)



full_amp_option.on_change = handle_amp_option
weapon_merging_option.on_change = handle_weapon_merge_option
skill_stacking_option.on_change = handle_skill_stacking_option

blr_options = [full_amp_option, weapon_merging_option, skill_stacking_option]
