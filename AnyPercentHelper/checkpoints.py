import inspect
import json
import os
import stat

import unrealsdk
from Mods.UserFeedback import TextInputBox
from Mods.AnyPercentHelper.utilities import Utilities
from Mods.AnyPercentHelper.glitch_manager import GlitchManager
from Mods.Commander import _GetPosition, _ApplyPosition


_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")
_MODDIR = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: None)))
_CONFIG_PATH = os.path.join(_MODDIR, 'config.json')
_STATE_PATH = os.path.join(_MODDIR, 'state.json')


class CheckpointSaver:
    """Class for saving read only copy of the current game and saving key values in local state.json file."""

    def __init__(self, new_save_name):
        self.PC = Utilities.get_current_player_controller()
        self.new_save_name = new_save_name
        self.save_dir = Utilities.get_save_dir_from_config(_CONFIG_PATH)
        self.current_file_name = self.PC.GetWillowGlobals().GetWillowSaveGameManager().LastLoadedFilePath
        self.current_file_path = self.get_current_file_path()
        self.temp_file_path = self.get_temp_file_path()
        self.new_file_path = self.get_next_open_save_path()
        self.glitches = GlitchManager()

    def get_current_file_path(self) -> str:
        """Current file path based on save directory and game provided filename. Will fail if config.json not
        set correctly."""
        current_file_path = os.path.join(self.save_dir, self.current_file_name)
        if not (os.path.exists(current_file_path) and os.path.isfile(current_file_path)):
            Utilities.feedback("Error finding current filepath")
            raise FileNotFoundError("Error finding current filepath")
        return current_file_path

    def get_temp_file_path(self) -> str:
        """Temp file path to rename current save."""
        temp_file_path = os.path.join(self.save_dir, "temp.sav")
        if os.path.exists(temp_file_path):
            os.chmod(temp_file_path, stat.S_IWRITE)
            os.remove(temp_file_path)
        return temp_file_path

    def get_next_open_save_path(self):
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
        return os.path.join(self.save_dir, filepath)

    def save_game_copy(self):
        """Saves current game state as read only, preserving previous file."""
        os.chmod(self.current_file_path, stat.S_IREAD)  # Set to read only
        os.rename(self.current_file_path, self.temp_file_path)  # Rename current save

        current_save_name = self.PC.GetPlayerUINamePreference()
        self.PC.SetPlayerUINamePreference(self.new_save_name)
        self.PC.SaveGame()  # Saves a new copy
        os.chmod(self.current_file_path, stat.S_IREAD)  # Set new file read only

        # Rename files
        os.rename(self.current_file_path, self.new_file_path)
        os.rename(self.temp_file_path, self.current_file_path)

        # Set name back to previous
        self.PC.SetPlayerUINamePreference(current_save_name)

    def get_game_state(self):
        """Gets the current state of the game for values that cannot be saved in the game save file."""
        state = {}
        # Buck up, anarchy, and free shots
        state['buckup_stacks'] = len(self.glitches.get_skill_stacks(['ShieldProbeBoost']))
        state['anarchy_stacks'] = self.glitches.get_anarchy_stacks()
        state['freeshot_stacks'] = len(self.glitches.get_skill_stacks(['Vladof Half Ammo']))

        # Weapons
        weapons = self.PC.GetPawnInventoryManager().GetEquippedWeapons()
        state['weapons_merged'] = []
        for weapon in weapons:
            if weapon:
                if len(weapon.ExternalAttributeModifiers) > 0:
                    state['weapons_merged'].append(weapon.QuickSelectSlot)
        state['active_weapon'] = self.PC.GetActiveOrBestWeapon().QuickSelectSlot

        # Position (using commander)
        state['position'] = _GetPosition(self.PC)
        return state

    def save_checkpoint(self):
        """Saves game and game state with the hash of the save file."""
        self.save_game_copy()
        state = self.get_game_state()
        unrealsdk.Log(state)

        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r") as f:
                existing = json.load(f)
        else:
            existing = {}

        # Set state data by hash value of the save file
        existing[Utilities.get_hash(self.new_file_path)] = state
        with open(_STATE_PATH, "w") as f:
            json.dump(existing, f)

    def get_game_state_from_state_file(self):
        """Retrieves game state from state.json based on the hash of the save file"""
        hash = Utilities.get_hash(self.current_file_path)
        with open(_STATE_PATH, "r") as f:
            states = json.load(f)
        if not states.get(hash):
            Utilities.feedback("No game state data found for this save file")
            return
        return states.get(hash)

    def load_game_state(self):
        """Loads the game state by applying glitches and the saved map position."""
        load_state = self.get_game_state_from_state_file()
        if not load_state:
            Utilities.feedback("No game state data found for this save file")
            return

        # Buck up, free shots, anarchy
        self.glitches.set_buckup_stacks(load_state['buckup_stacks'])
        self.glitches.set_anarchy_stacks(load_state['anarchy_stacks'])
        self.glitches.set_infinite_ammo_stacks(load_state['freeshot_stacks'])

        # Weapon merges
        weapons = self.PC.GetPawnInventoryManager().GetEquippedWeapons()
        merge_msg = ''
        prefix = '\t'
        for weapon in weapons:
            if weapon and weapon.QuickSelectSlot in load_state['weapons_merged']:
                weapon.ApplyAllExternalAttributeEffects()
                merge_msg = merge_msg + prefix + weapon.GetShortHumanReadableName()
                prefix = '\n\t'

        # Position (using commander)
        _ApplyPosition(self.PC, load_state['position'])

        Utilities.feedback(
            f"Game State Loaded" +
            f"\nBuck Up Stacks: {load_state['buckup_stacks']}" +
            f"\nAnarchy Stacks: {load_state['anarchy_stacks']}" +
            f"\nFree Shot Stacks: {load_state['freeshot_stacks']}" +
            f"\nWeapons Merged:" +
            f"\n{merge_msg}"
        )


class SaveNameInput(TextInputBox):
    """Input box class whose only responsibility is to set the message and call the saver class for handling"""

    def OnSubmit(self, Message: str) -> None:
        """Override base class method. This is called when the text box is closed."""
        if Message:
            checkpoint_saver = CheckpointSaver(Message)
            checkpoint_saver.save_checkpoint()
