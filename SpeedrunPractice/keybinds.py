from dataclasses import dataclass
from typing import Callable, List, Optional

from Mods.Commander.Builtin import _RestorePosition
from Mods.ModMenu import Keybind
from Mods.SpeedrunPractice.checkpoints import CheckpointSaver, text_input_checkpoint
from Mods.SpeedrunPractice.gear import GearRandomizer
from Mods.SpeedrunPractice.skills import activate_skill, get_attribute_value, get_skill_stacks, set_designer_attribute_value, \
    set_skill_stacks, text_input_stacks, trigger_kill_skills
from Mods.SpeedrunPractice.utilities import RunCategory, PlayerClass, Singleton, feedback, get_current_player_controller
from Mods.SpeedrunPractice.options import SPOptions
from unrealsdk import FindAll


@dataclass
class SPKeybind(Keybind):
    order: int = 100
    callback: Optional[Callable[[], None]] = None


class SPKeybinds(Singleton):

    def __init__(self, options: SPOptions):
        self.options = options
        self.player_class: Optional[PlayerClass] = None
        self.run_category: Optional[RunCategory] = None

        self.Buckup = SPKeybind("Set Buckup Stacks", "None", callback=set_buckup_stacks, IsHidden=True, order=1)
        self.Anarchy = SPKeybind("Set Anarchy Stacks", "None", callback=set_anarchy_stacks, IsHidden=True, order=2)

        self.FreeShotStacks = SPKeybind("Set Free Shot Stacks", "None", callback=set_free_shot_stacks, IsHidden=True, order=10)
        self.SmasherChanceStacks = SPKeybind("Set Smasher Chance Stacks", "None", callback=set_smasher_chance_stacks, IsHidden=True,
                                             order=11)
        self.SmasherSmashStacks = SPKeybind("Set Smasher SMASH Stacks", "None", callback=set_smasher_SMASH_stacks, IsHidden=True, order=12)
        self.MergeWeapons = SPKeybind("Merge Equipped Weapons", "None", callback=merge_all_equipped_weapons, IsHidden=True, order=13)
        self.RandomizeGear = SPKeybind("Randomize Any% Gear", "None", callback=randomize_any_p_gear, IsHidden=True, order=14)
        self.ShowState = SPKeybind("Show Stacks/Crit", "None", callback=self.show_state, IsHidden=True, order=20)

        self.ResetGunzerk = SPKeybind("Reset Gunzerk and Weapons", "None", callback=reset_gunzerk_and_weapons, IsHidden=True, order=30)
        self.ResetAndTrigger = SPKeybind("Reset to Commander Position and Trigger Skills", "None",
                                         callback=self.reset_to_position_and_trigger_skills,
                                         IsHidden=True, order=31)

        self.SaveCheckpoint = SPKeybind("Save Checkpoint", "None", callback=self.save_checkpoint, order=40)
        self.LoadCheckpoint = SPKeybind("Load Checkpoint State", "None", callback=self.load_checkpoint, order=41)
        self.TouchSave = SPKeybind("Move Current Save to Top", "None", callback=touch_file, order=42)

    @property
    def Keybinds(self) -> List[SPKeybind]:
        return [self.Buckup, self.Anarchy, self.RandomizeGear, self.FreeShotStacks, self.SmasherChanceStacks, self.SmasherSmashStacks,
                self.MergeWeapons, self.ShowState, self.ResetGunzerk, self.ResetAndTrigger, self.SaveCheckpoint, self.LoadCheckpoint,
                self.TouchSave]

    def enable(self, player_class_arg: PlayerClass, run_category_arg: RunCategory):
        self.player_class = player_class_arg
        self.run_category = run_category_arg

        self.enable_keybinds([self.SaveCheckpoint, self.LoadCheckpoint, self.TouchSave])

        if self.player_class == PlayerClass.Gaige:
            self.enable_keybinds([self.Buckup, self.Anarchy])
            if self.run_category == RunCategory.AnyPercent:
                self.enable_keybinds([self.RandomizeGear])

        if self.run_category in [RunCategory.AnyPercent, RunCategory.AllQuests]:
            self.enable_keybinds([self.FreeShotStacks, self.MergeWeapons, self.ShowState])

        if self.run_category == RunCategory.AllQuests:
            self.enable_keybinds([self.SmasherChanceStacks, self.SmasherSmashStacks])

        if self.player_class == PlayerClass.Salvador and self.run_category == RunCategory.Geared:
            self.enable_keybinds([self.ResetGunzerk, self.ResetAndTrigger])

    def disable(self):
        self.player_class = None
        self.run_category = None

        self.disable_keybinds(self.Keybinds)

    def enable_keybinds(self, keybinds: List[SPKeybind]):
        for kb in keybinds:
            kb.IsHidden = False
            kb.OnPress = kb.callback

    def disable_keybinds(self, keybinds: List[SPKeybind]):
        for kb in keybinds:
            kb.IsHidden = True
            kb.OnPress = None

    def reset_to_position_and_trigger_skills(self):
        PC = get_current_player_controller()
        reset_gunzerk_and_weapons()
        _RestorePosition()
        if self.options.Incite.CurrentValue:
            set_skill_stacks(PC, 1, 'GD_Mercenary_Skills.Brawn.Incite_Active')
        if self.options.LockedAndLoaded.CurrentValue:
            set_skill_stacks(PC, 1, 'GD_Mercenary_Skills.Gun_Lust.LockedAndLoaded_Active')
        if self.options.KillSkills.CurrentValue:
            trigger_kill_skills(PC)

    def show_state(self) -> None:
        """Show current status of key values"""
        PC = get_current_player_controller()
        msg = ''
        if self.player_class == PlayerClass.Gaige:
            msg += f"\nBuckup Stacks: {len(get_skill_stacks(PC, ['Skill_ShieldBoost_Player']))}"
        msg += f"\nFree Shot Stacks: {len(get_skill_stacks(PC, ['Skill_VladofHalfAmmo']))}"
        if self.run_category == RunCategory.AllQuests:
            msg += f"\nSmasher Chance Stacks: {len(get_skill_stacks(PC, ['Skill_EvilSmasher']))}"
            msg += f"\nSmasher SMASH Stacks: {len(get_skill_stacks(PC, ['Skill_EvilSmasher_SMASH']))}"
        msg += f"\nCritical Hit Bonus: {round(get_attribute_value(PC, 'D_Attributes.GameplayAttributes.PlayerCriticalHitBonus'), 2)}"
        feedback(PC, msg)

    def save_checkpoint(self):
        if self.player_class and self.run_category:
            text_input_checkpoint("Character Save Name", self.player_class, self.run_category)
        else:
            feedback(get_current_player_controller(), "Unable to save checkpoint for this character")

    def load_checkpoint(self):
        if self.player_class and self.run_category:
            saver = CheckpointSaver(None, self.player_class, self.run_category)
            saver.load_game_state()
        else:
            feedback(get_current_player_controller(), "Unable to load checkpoint for this character")


def merge_all_equipped_weapons() -> None:
    """Applies external attribute effects from all weapons currently equipped. Used for crit bonus in runs."""
    PC = get_current_player_controller()
    weapons = PC.GetPawnInventoryManager().GetEquippedWeapons()
    msg = ''
    for weapon in weapons:
        if weapon:
            weapon.ApplyAllExternalAttributeEffects()
            msg = msg + '\n' + weapon.GetShortHumanReadableName()
    feedback(PC, f"Bonuses from the following weapons are applied: {msg}")


def set_free_shot_stacks():
    text_input_stacks(set_skill_stacks, "Set Free Shot Stacks", "GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo")


def set_smasher_chance_stacks():
    text_input_stacks(set_skill_stacks, "Set Smasher Chance Stacks", "GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher")


def set_smasher_SMASH_stacks():
    text_input_stacks(set_skill_stacks, "Set Smasher SMASH Stacks", "GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher_SMASH")


def randomize_any_p_gear():
    gear_r = GearRandomizer()
    gear_r.randomize_gear()


def reset_gunzerk_and_weapons():
    PC = get_current_player_controller()
    ammo_pools = FindAll('AmmoResourcePool')
    for pool in ammo_pools[1:]:
        if pool.Definition:
            if pool.Definition.Resource.ResourceName == 'Rockets':
                pool.SetCurrentValue(pool.GetMaxValue())

    def _drop_pickup_weapon(weapon):
        inventory_manager.RemoveFromInventory(weapon)
        inventory_manager.AddInventory(weapon, True)

    PC.ResetSkillCooldown()

    inventory_manager = PC.GetPawnInventoryManager()
    weapons = inventory_manager.GetEquippedWeapons()
    weapons_by_slot = {weapon.QuickSelectSlot: weapon for weapon in weapons if weapon}

    # Canceling gunzerk like this because using a func directly crashes the game sometimes
    for slot in [1, 2, 3, 4]:  # Cancel gunzerk
        if weapons_by_slot.get(slot):
            inventory_manager.RemoveFromInventory(weapons_by_slot[slot])
    for slot in [1, 2, 3, 4]:  # Add weapons back in
        if weapons_by_slot.get(slot):
            inventory_manager.AddInventory(weapons_by_slot[slot], False)
    for slot in [3, 4, 1, 2]:
        if weapons_by_slot.get(slot):
            _drop_pickup_weapon(weapons_by_slot[slot])
    PC.EquipWeaponFromSlot(3)


def set_buckup_stacks():
    text_input_stacks(set_skill_stacks, "Set Buckup Stacks", "GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player")


def set_anarchy_stacks():
    text_input_stacks(set_designer_attribute_value, "Set Anarchy Stacks", "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks")


def touch_file():
    saver = CheckpointSaver(None)
    saver.touch_current_save()
