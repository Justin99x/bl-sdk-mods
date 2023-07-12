import hashlib
import json
import unrealsdk
from typing import cast

_DefaultGameInfo = unrealsdk.FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")


class Utilities:
    """Class for organizing various useful methods"""

    @staticmethod
    def get_save_dir_from_config(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        return config["LocalGameSaves"]

    @staticmethod
    def get_current_player_controller() -> unrealsdk.UObject:
        """Returns the local player"""
        return cast(unrealsdk.UObject, unrealsdk.GetEngine().GamePlayers[0].Actor)

    @staticmethod
    def clone_obj(new_name, in_class_str, template_obj_str):
        """Creates a fresh object based on the class name and a template object defintion"""
        obj_to_clone = unrealsdk.FindObject(in_class_str, template_obj_str)
        return unrealsdk.ConstructObject(Class=in_class_str, Outer=obj_to_clone.Outer, Name=new_name,
                                         Template=obj_to_clone)

    @staticmethod
    def get_hash(filepath):
        with open(filepath, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.new("sha256", file_contents).hexdigest()

        return file_hash

    @classmethod
    def feedback(cls, feedback):
        """Presents a "training" message to the user with the given string"""
        PC = cls.get_current_player_controller()
        HUDMovie = PC.GetHUDMovie()
        if HUDMovie is None:
            return

        duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
        HUDMovie.ClearTrainingText()
        HUDMovie.AddTrainingText(feedback, "Gaige Any% Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                                 True)
