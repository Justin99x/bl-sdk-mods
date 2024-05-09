from typing import Optional

from Mods.SpeedrunPractice.skills import get_skill_stacks
from Mods.SpeedrunPractice.utilities import RunCategory, PlayerClass, Singleton, get_current_player_controller
from unrealsdk import FStruct, FindObject, RemoveHook, RunHook, UFunction, UObject


class SPHooks(Singleton):

    def __init__(self):
        self.player_class: Optional[PlayerClass] = None
        self.run_category: Optional[RunCategory] = None

    def enable(self, player_class_arg: PlayerClass, run_category_arg: RunCategory):
        self.player_class = player_class_arg
        self.run_category = run_category_arg

        if self.run_category in [RunCategory.AllQuests, RunCategory.AnyPercent]:
            RunHook("Engine.Actor.TriggerGlobalEventClass", 'SpeedrunPractice', set_pickup_radius_and_skill_stacking)
            RunHook('WillowGame.WillowPlayerController.ModalGameMenuOpening', 'SpeedrunPractice', allow_weapon_merge)
            RunHook('WillowGame.WillowInventoryManager.RemoveFromInventory', 'SpeedrunPractice', allow_drop_stacking)
        if self.run_category == RunCategory.AnyPercent:
            RunHook('WillowGame.WillowPlayerController.SaveGame', 'SpeedrunPractice', enable_divide_fast_travel)
            RunHook('WillowGame.Skill.Resume', 'SpeedrunPractice', apply_full_amp)
            RunHook('WillowGame.WillowWeapon.OnEquip', 'SpeedrunPractice', apply_full_amp)

    def disable(self):
        self.player_class = None
        self.run_category = None

        RemoveHook("Engine.Actor.TriggerGlobalEventClass", 'SpeedrunPractice')
        RemoveHook('WillowGame.WillowPlayerController.SaveGame', 'SpeedrunPractice')
        RemoveHook('WillowGame.Skill.Resume', 'SpeedrunPractice')
        RemoveHook('WillowGame.WillowWeapon.OnEquip', 'SpeedrunPractice')
        RemoveHook('WillowGame.WillowPlayerController.ModalGameMenuOpening', 'SpeedrunPractice')
        RemoveHook('WillowGame.WillowInventoryManager.RemoveFromInventory', 'SpeedrunPractice')


def set_pickup_radius_and_skill_stacking(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """Mimic version 1.1 and 1.3.1 behavior on bulk pickup radius and skill stacking. These reset on level load so no need to disable"""
    if params.InEventClass.Name == 'WillowSeqEvent_PlayerJoined':
        PC = get_current_player_controller()
        PC.ConsoleCommand(f"set GD_Globals.General.Globals PickupRadius 200")
        PC.ConsoleCommand(f"set Behavior_ActivateSkill bNoSkillStacking False")
    return True


def enable_divide_fast_travel(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """Enables Three Horns Divide FT as soon as Divide mission reached, allows skipping station like in patch 1.1"""
    if 'IceEast' not in caller.ActivatedTeleportersList:
        if caller.GetActivePlotCriticalMissionNumber() >= 4:
            temp = list(caller.ActivatedTeleportersList)
            temp.append('IceEast')
            caller.ActivatedTeleportersList = temp
    return True


def apply_full_amp(caller: UObject, function: UFunction, params: FStruct):
    """
    Apply full amp damage to every pellet. We replace the skill scale constant with the
    projectile count to effectively give every pellet full amp damage.
    """
    PC = get_current_player_controller()
    active_weapon = PC.Pawn.Weapon
    if not active_weapon:
        return True
    projectiles_attr = FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponProjectilesPerShot")
    projectiles = projectiles_attr.GetValue(active_weapon)[0]

    amp_skills = get_skill_stacks(PC, ['Impact_Shield_Skill_Legendary', 'Impact_Shield_Skill'])
    for amp_skill in amp_skills:
        if amp_skill.SkillState == 1:
            weapon_damage_effect = [effect for effect in amp_skill.SkillEffects if
                                    effect.EffectData.AttributeToModify.Name == "WeaponDamage"][0]
            weapon_damage_effect.EffectData.BaseModifierValue.BaseValueScaleConstant = projectiles
    return True


def allow_weapon_merge(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """Allow merging weapons to keep crit bonuses, healing, etc. This follows the exact logic that made
    the glitch possible in the first place. They later added the ForcePutDownInactiveWeapon call to the
    ModalGameMenuOpening method to fix it, so we're just blocking it."""

    def block_putdown(caller: UObject, function: UFunction, params: FStruct) -> bool:
        return False

    RunHook('WillowGame.WillowWeapon.ForcePutDownInactiveWeapon', 'SpeedrunPractice', block_putdown)
    caller.ModalGameMenuOpening()
    RemoveHook('WillowGame.WillowWeapon.ForcePutDownInactiveWeapon', 'SpeedrunPractice')
    return False


def allow_drop_stacking(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """Allow dropping weapons to keep skill stacks. This follows the exact logic that made
    the glitch possible in the first place. They later added the OnUnequip call to the
    RemoveFromInventory method to fix it, so we're just blocking it."""

    def block_onunequip(caller: UObject, function: UFunction, params: FStruct) -> bool:
        return False

    RunHook('WillowGame.WillowWeapon.OnUnequip', 'SpeedrunPractice', block_onunequip)
    caller.RemoveFromInventory(params.ItemToRemove, params.bCanDrop)
    RemoveHook('WillowGame.WillowWeapon.OnUnequip', 'SpeedrunPractice')
    return False
