import hashlib
import json
from enum import Enum

from unrealsdk import Log, FindObject, UObject, GetEngine, ConstructObject
from typing import Type, cast

_DefaultGameInfo = FindObject("WillowCoopGameInfo", "WillowGame.Default__WillowCoopGameInfo")


def get_save_dir_from_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    return config["LocalGameSaves"]


def get_current_player_controller() -> UObject:
    """Returns the local player"""
    return cast(UObject, GetEngine().GamePlayers[0].Actor)


def clone_obj(new_name, in_class_str, template_obj_str):
    """Creates a fresh object based on the class name and a template object defintion"""
    obj_to_clone = FindObject(in_class_str, template_obj_str)
    return ConstructObject(Class=in_class_str, Outer=obj_to_clone.Outer, Name=new_name,
                           Template=obj_to_clone)


def get_hash(filepath):
    with open(filepath, "rb") as f:
        file_contents = f.read()
        file_hash = hashlib.new("sha256", file_contents).hexdigest()

    return file_hash


def get_position(PC):
    location = PC.Pawn.Location
    rotation = PC.Rotation
    return {
        "X": location.X, "Y": location.Y, "Z": location.Z,
        "Pitch": rotation.Pitch, "Yaw": rotation.Yaw
    }


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


def feedback(PC, feedback):
    """Presents a "training" message to the user with the given string"""
    HUDMovie = PC.GetHUDMovie()
    if HUDMovie is None:
        return

    duration = 3.0 * _DefaultGameInfo.GameSpeed  # We will be displaying the message for two *real time* seconds.
    HUDMovie.ClearTrainingText()
    HUDMovie.AddTrainingText(feedback, "Speedrun Practice", duration, (), "", False, 0, PC.PlayerReplicationInfo,
                             True)


def try_parse_int(s, default=None):
    try:
        return int(s)
    except ValueError:
        Log(f"Unable to parse input {s}, setting value to 0")
        return 0


def enum_from_value(cls: Type[Enum], value):
    for member in cls:
        if member.value == value:
            return member
    raise ValueError(f"{value} is not a valid value for {cls.__name__}")


class PlayerClass(Enum):
    Gaige = "CharClass_Mechromancer"
    Salvador = "CharClass_Mercenary"
    Axton = "CharClass_Soldier"
    Zero = "CharClass_Assassin"
    Krieg = "CharClass_LilacPlayerClass"
    Maya = "CharClass_Siren"

class RunCategory(Enum):
    AnyPercent = "Any% (1.1)"
    AllQuests = "All Quests (1.3.1)"
    Geared = "Geared Sal (2.0)"

class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
