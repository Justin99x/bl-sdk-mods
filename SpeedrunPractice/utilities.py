import hashlib
import json
from unrealsdk import Log, FindObject, UObject, GetEngine, ConstructObject
from typing import cast


_DefaultGameInfo = FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")


class Utilities:
    """Class for organizing various useful methods"""

    @staticmethod
    def get_save_dir_from_config(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        return config["LocalGameSaves"]

    @staticmethod
    def get_current_player_controller() -> UObject:
        """Returns the local player"""
        return cast(UObject, GetEngine().GamePlayers[0].Actor)

    @staticmethod
    def clone_obj(new_name, in_class_str, template_obj_str):
        """Creates a fresh object based on the class name and a template object defintion"""
        obj_to_clone = FindObject(in_class_str, template_obj_str)
        return ConstructObject(Class=in_class_str, Outer=obj_to_clone.Outer, Name=new_name,
                                         Template=obj_to_clone)

    @staticmethod
    def get_hash(filepath):
        with open(filepath, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.new("sha256", file_contents).hexdigest()

        return file_hash

    @staticmethod
    def get_position(PC):
        location = PC.Pawn.Location
        rotation = PC.Rotation
        return {
            "X": location.X, "Y": location.Y, "Z": location.Z,
            "Pitch": rotation.Pitch, "Yaw": rotation.Yaw
        }

    @staticmethod
    def apply_position(PC, position):
        location = position["X"], position["Y"], position["Z"]
        rotation = position["Pitch"], position["Yaw"], 0


        _, vehicle = PC.IsUsingVehicleEx(True)
        if vehicle is None:
            PC.NoFailSetPawnLocation(PC.Pawn, location)
        else:
            pawn = vehicle.GetPawnToTeleport()
            pawn.Mesh.SetRBPosition(location)
            pawn.Mesh.SetRBRotation(rotation)
        PC.ClientSetRotation(rotation)

    @classmethod
    def feedback(cls, feedback):
        """Presents a "training" message to the user with the given string"""
        PC = cls.get_current_player_controller()
        HUDMovie = PC.GetHUDMovie()
        if HUDMovie is None:
            return

        duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
        HUDMovie.ClearTrainingText()
        HUDMovie.AddTrainingText(feedback, "Speedrun Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                                 True)

    @staticmethod
    def try_parse_int(s, default=None):
        try:
            return int(s)
        except ValueError:
            Log(f"Unable to parse input {s}, setting value to 0")
            return 0
