import inspect
import os
import stat
from pathlib import Path
from typing import Optional

from unrealsdk import FindObject

from Mods.SpeedrunPractice.skills import get_skill_stacks, get_designer_attribute_value, set_designer_attribute_value, set_skill_stacks
from Mods.SpeedrunPractice.utilities import apply_position, feedback, get_current_player_controller, get_position, \
    get_save_dir_from_config
from Mods.SpeedrunPractice.utilities import RunCategory, PlayerClass
from Mods.UserFeedback import TextInputBox

_DefaultGameInfo = FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")
_MODDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))
_CONFIG_PATH = os.path.join(_MODDIR, 'config.json')
_STATE_PATH = os.path.join(_MODDIR, 'state.json')

PLAYER_STATS_MAP = {
    'STAT_PLAYER_ZRESERVED_DLC_INT_BZ': 'anarchy_stacks',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CA': 'buckup_stacks',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CB': 'freeshot_stacks',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CC': 'weapons',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CD': 'active_weapon',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CE': 'smasher_stacks',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CF': 'X',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CG': 'Y',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CH': 'Z',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CI': 'Pitch',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CJ': 'Yaw',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CK': 'weapon1_clip',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CL': 'weapon2_clip',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CM': 'weapon3_clip',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CN': 'weapon4_clip',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CO': 'SMASH_stacks',
    'STAT_PLAYER_ZRESERVED_DLC_INT_CP': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CQ': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CR': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CS': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CT': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CU': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CV': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CW': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CX': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CY': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_CZ': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DA': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DB': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DC': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DD': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DE': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DF': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DG': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DH': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DI': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DJ': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DK': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DL': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DM': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DN': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DO': None,
    'STAT_PLAYER_ZRESERVED_DLC_INT_DP': None
}


class CheckpointSaver:
    """Class for saving read only copy of the current game and saving key values as player stats"""

    def __init__(self, new_save_name, player_class: Optional[PlayerClass] = None, run_category: Optional[RunCategory] = None):
        self.PC = get_current_player_controller()
        self.new_save_name = new_save_name
        self.save_dir = get_save_dir_from_config(_CONFIG_PATH)
        self.current_file_name = self.PC.GetWillowGlobals().GetWillowSaveGameManager().LastLoadedFilePath
        self.current_file_path = self.get_current_file_path()
        self.new_filename = self.get_next_open_filename()
        self.player_class = player_class
        self.run_category = run_category

    def get_current_file_path(self) -> str:
        """Current file path based on save directory and game provided filename. Will fail if config.json not
        set correctly."""
        current_file_path = os.path.join(self.save_dir, self.current_file_name)
        if not (os.path.exists(current_file_path) and os.path.isfile(current_file_path)):
            feedback(self.PC, "Error finding current filepath")
            raise FileNotFoundError("Error finding current filepath")
        return current_file_path

    def get_next_open_filename(self):
        """Finds next available save number based on files in the save directory. Increments by 1."""
        try:
            path_num = int(self.current_file_name[4:8])
            decimal = True
        except:
            path_num = int(self.current_file_name[4:8], 16)
            decimal = False
        while True:
            path_num = path_num + 1
            if decimal:
                filepath = "Save" + f"{path_num}".zfill(4).upper() + ".sav"
            else:
                filepath = "Save" + f"{path_num:x}".zfill(4).upper() + ".sav"
            if not os.path.exists(os.path.join(self.save_dir, filepath)):
                break
        return filepath

    def save_game_copy(self):
        current_save_name = self.PC.GetPlayerUINamePreference()
        self.PC.SetPlayerUINamePreference(self.new_save_name)
        self.PC.SaveGame(self.new_filename)
        os.chmod(os.path.join(self.save_dir, self.new_filename), stat.S_IREAD)

        self.PC.SetPlayerUINamePreference(current_save_name)
        self.PC.SaveGame(self.current_file_name)

    def set_player_stats(self, state):
        """Sets the player stats on the PC, intent is to save game right after"""
        stats = self.PC.PlayerStats
        for stats_name, name in PLAYER_STATS_MAP.items():
            stats.SetIntStat(stats_name, state.get(name, 0))

    def get_player_stats(self):
        """Get player stats - for these it will be what was loaded from save file"""
        stats = self.PC.PlayerStats
        state = {}
        for stats_name, name in PLAYER_STATS_MAP.items():
            state[name] = stats.GetIntStat(stats_name)
        state['weapons'] = [int(val) for val in str(state['weapons']).zfill(5)]
        state['position'] = {}
        state['position']['X'] = state['X'] / 100
        state['position']['Y'] = state['Y'] / 100
        state['position']['Z'] = state['Z'] / 100
        state['position']['Pitch'] = int(state['Pitch'] / 100)
        state['position']['Yaw'] = int(state['Yaw'] / 100)
        return state

    def get_game_state(self):
        """Gets the current state of the game for values that cannot be saved in the game save file."""
        state = {}
        # Buck up, anarchy, and free shots
        if self.player_class == PlayerClass.Gaige:
            state['buckup_stacks'] = len(get_skill_stacks(self.PC, ['Skill_ShieldBoost_Player']))
            state['anarchy_stacks'] = int(
                get_designer_attribute_value(self.PC, 'GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks'))
        if self.run_category == RunCategory.AllQuests:
            state['smasher_stacks'] = len(get_skill_stacks(self.PC, ['Skill_EvilSmasher']))
            state['SMASH_stacks'] = len(get_skill_stacks(self.PC, ['Skill_EvilSmasher_SMASH']))
        if self.run_category in [RunCategory.AnyPercent, RunCategory.AllQuests]:
            state['freeshot_stacks'] = len(get_skill_stacks(self.PC, ['Skill_VladofHalfAmmo']))

            # Weapons - don't want for current patch.
            weapons = self.PC.GetPawnInventoryManager().GetEquippedWeapons()

            state['weapons'] = [0, 0, 0, 0, 0]  # Active weapon slot followed by bools for merged weapons or not.
            state['weapons'][0] = self.PC.GetActiveOrBestWeapon().QuickSelectSlot
            for weapon in weapons:
                if weapon:
                    state[f'weapon{weapon.QuickSelectSlot}_clip'] = weapon.ReloadCnt
                    if len(weapon.ExternalAttributeModifiers) > 0:
                        state['weapons'][weapon.QuickSelectSlot] = 1
            state['weapons'] = int(''.join(str(val) for val in state['weapons']))

        position = get_position(self.PC)
        state['X'] = int(position['X'] * 100)
        state['Y'] = int(position['Y'] * 100)
        state['Z'] = int(position['Z'] * 100)
        state['Pitch'] = int(position['Pitch'] * 100)
        state['Yaw'] = int(position['Yaw'] * 100)
        return state

    def load_game_state(self):
        """Loads the game state by applying glitches and the saved map position."""
        load_state = self.get_player_stats()
        if load_state['position']['X'] == 0 and load_state['position']['Y'] == 0:
            feedback(self.PC, "No game state data found for this save file")
            return

        gaige_msg, free_shot_msg, smasher_msg, merge_msg = '', '', '', ''

        # Equipped weapon and clip sizes
        if self.run_category in [RunCategory.AnyPercent, RunCategory.AllQuests]:
            inventory_manager = self.PC.GetPawnInventoryManager()
            weapons = inventory_manager.GetEquippedWeapons()
            for weapon in weapons:
                # Use drop pickups to get our desired active weapon in place
                if weapon and load_state['weapons'][0] != weapon.QuickSelectSlot:
                    inventory_manager.RemoveFromInventory(weapon)
                    inventory_manager.AddInventory(weapon, False)
                # Set clip sizes
                if weapon:
                    weapon.ReloadCnt = load_state[f'weapon{weapon.QuickSelectSlot}_clip']
                    weapon.LastReloadCnt = weapon.ReloadCnt

            # Merge weapons
            merge_msg = f"\nWeapons Merged:"
            for weapon in weapons:
                if weapon and load_state['weapons'][weapon.QuickSelectSlot] == 1:
                    weapon.ApplyAllExternalAttributeEffects()
                    merge_msg = merge_msg + '\n\t' + weapon.GetShortHumanReadableName()

            # Buck up, free shots, anarchy, and smasher. After weapon stuff so no issues with deactivations.
            set_skill_stacks(self.PC, load_state['freeshot_stacks'], 'GD_Weap_Launchers.Skills.Skill_VladofHalfAmmo')
            free_shot_msg = f"\nFree Shot Stacks: {load_state['freeshot_stacks']}"

        if self.run_category == RunCategory.AllQuests:
            set_skill_stacks(self.PC, load_state['smasher_stacks'], 'GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher')
            set_skill_stacks(self.PC, load_state['SMASH_stacks'], 'GD_Weap_AssaultRifle.Skills.Skill_EvilSmasher_SMASH')
            smasher_msg = f"\nSmasher Chance Stacks: {load_state['smasher_stacks']}"
            smasher_msg += f"\nSmasher SMASH Stacks: {load_state['SMASH_stacks']}"

        if self.player_class == PlayerClass.Gaige:
            set_skill_stacks(self.PC, load_state['buckup_stacks'], 'GD_Tulip_DeathTrap.Skills.Skill_ShieldBoost_Player')
            set_designer_attribute_value(self.PC, load_state['anarchy_stacks'],
                                         'GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks')
            gaige_msg += f"\nBuck Up Stacks: {load_state['buckup_stacks']}"
            gaige_msg += f"\nAnarchy Stacks: {load_state['anarchy_stacks']}"

        # Position
        apply_position(self.PC, load_state['position'])

        msg = f"Game State Loaded" + gaige_msg + free_shot_msg + smasher_msg + merge_msg
        feedback(self.PC, msg)

    def save_checkpoint(self):
        """Saves game and game state"""
        state = self.get_game_state()
        self.set_player_stats(state)
        self.save_game_copy()

    def touch_current_save(self):
        Path(self.get_current_file_path()).touch(exist_ok=True)

def text_input_checkpoint(title: str, player_class: PlayerClass, run_category: RunCategory) -> None:
    """Handle input box creation for various actions"""
    input_box = TextInputBox(title, PausesGame=True)

    def OnSubmit(msg: str) -> None:
        if msg:
            saver = CheckpointSaver(msg, player_class, run_category)
            saver.save_checkpoint()

    input_box.OnSubmit = OnSubmit
    input_box.Show()
