from typing import List, Optional

from Mods import ModMenu
from Mods.ModMenu.Options import Base
from Mods.SpeedrunPractice.utilities import RunCategory, PlayerClass, Singleton, get_current_player_controller
from unrealsdk import FStruct, FindAll, FindObject, GetEngine, Log, RemoveHook, RunHook, UFunction, UObject


class SPOptions(Singleton):

    def __init__(self):
        self.player_class: Optional[PlayerClass] = None
        self.run_category: Optional[RunCategory] = None

        self.RunCatOption = ModMenu.Options.Spinner(
            Caption="Run Category",
            Description="Simulates functionality of older patches.",
            StartingValue="Any% (1.1)",
            Choices=("Any% (1.1)", "All Quests (1.3.1)", "Geared Sal (2.0)"),
            IsHidden=True
        )
        self.JakobsAutoFire = ModMenu.Options.Boolean(
            Caption="Automatic Jakobs Shotguns",
            Description="Makes Jakobs shotguns automatic to mimic freescroll macro functionality",
            StartingValue=False,
            Choices=("Off", "On"),
            IsHidden=True
        )
        self.KillSkills = ModMenu.Options.Boolean(
            Caption="Trigger Kill Skills on Reset",
            Description="When Reset to Position and Trigger Skills is pressed, trigger kill skills",
            StartingValue=False,
            Choices=("Off", "On"),
            IsHidden=True
        )
        self.Incite = ModMenu.Options.Boolean(
            Caption="Trigger Incite on Reset",
            Description="When Reset to Position and Trigger Skills is pressed, trigger Incite",
            StartingValue=False,
            Choices=("Off", "On"),
            IsHidden=True
        )
        self.LockedAndLoaded = ModMenu.Options.Boolean(
            Caption="Trigger Locked and Loaded on Reset",
            Description="When Reset to Position and Trigger Skills is pressed, trigger Locked and Loaded",
            StartingValue=False,
            Choices=("Off", "On"),
            IsHidden=True
        )
        self.TravelPortalDisabled = ModMenu.Options.Boolean(
            Caption="Disable Travel Portal",
            Description="Disables blue tunnel animation when loading into a map",
            StartingValue=False,
            Choices=("Off", "On"),
            IsHidden=True
        )
        self.PlayerRunCategory = ModMenu.Options.Hidden(
            Caption="Store last run category for character",
            Description="Allow run category to be set from character load. Whatever category was last used by character will be loaded.",
            StartingValue={
                PlayerClass.Gaige.value: RunCategory.AnyPercent.value,
                PlayerClass.Salvador.value: RunCategory.Geared.value,
                PlayerClass.Zero.value: RunCategory.AnyPercent.value,
                PlayerClass.Krieg.value: RunCategory.AnyPercent.value,
                PlayerClass.Maya.value: RunCategory.AnyPercent.value,
                PlayerClass.Axton.value: RunCategory.AnyPercent.value,
            },
        )


    @property
    def Options(self) -> List[Base]:
        return [self.RunCatOption, self.JakobsAutoFire, self.KillSkills, self.Incite, self.LockedAndLoaded, self.PlayerRunCategory,
                self.TravelPortalDisabled]

    def enable(self, player_class_arg: PlayerClass, run_category_arg: RunCategory):
        self.player_class = player_class_arg
        self.run_category = run_category_arg

        self.enable_options([self.RunCatOption, self.TravelPortalDisabled])
        handle_travel_portal(self.TravelPortalDisabled.CurrentValue)

        if self.run_category in [RunCategory.AnyPercent, RunCategory.AllQuests]:
            handle_jakobs_auto(self.JakobsAutoFire.CurrentValue)
            handle_expansion_fast_travel(True)
            self.enable_options([self.JakobsAutoFire])

        if self.player_class == PlayerClass.Salvador and self.run_category == RunCategory.Geared:
            self.enable_options([self.KillSkills, self.Incite, self.LockedAndLoaded])

    def disable(self):
        self.player_class = None
        self.run_category = None

        handle_jakobs_auto(False)
        handle_expansion_fast_travel(False)
        handle_travel_portal(False)

        self.disable_options(self.Options)

    def enable_options(self, options: List[Base]):
        for option in options:
            option.IsHidden = False

    def disable_options(self, options: List[Base]):
        for option in options:
            option.IsHidden = True


def handle_expansion_fast_travel(disable_expansions: bool):
    """ Remove expansions from DLC manager so that they don't show up in FT. Add them back in if the option is
    turned back off."""
    dlc_manager = GetEngine().GetDLCManager()
    if disable_expansions:
        dlc_manager.Expansions = []
    else:
        dlc_manager.Expansions = FindAll("DownloadableExpansionDefinition")[1:]


def handle_jakobs_auto(new_value: bool) -> None:
    """Turns automatic Jakobs shotguns on or off. Used to mimic functionality of free scroll macro."""
    PC = get_current_player_controller()
    weapons = FindAll('WillowWeapon')
    autoburst_attribute_def = FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponAutomaticBurstCount")
    jakobs_shotguns = [weapon for weapon in weapons if
                       weapon.DefinitionData.WeaponTypeDefinition is not None and weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun']
    if new_value:
        PC.ConsoleCommand(
            f"set WeaponTypeDefinition'GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun' AutomaticBurstCount 0")
        for js in jakobs_shotguns:
            autoburst_attribute_def.SetAttributeBaseValue(js, 0)
    else:
        PC.ConsoleCommand(
            f"set WeaponTypeDefinition'GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun' AutomaticBurstCount 1")
        for js in jakobs_shotguns:
            autoburst_attribute_def.SetAttributeBaseValue(js, 1)


def handle_travel_portal(disable_portal: bool):
    """ Disable travel animation for faster practice"""

    def disable_portal_hook(caller: UObject, function: UFunction, params: FStruct) -> bool:
        holding = FindObject('HoldingAreaDestination', 'Loader.TheWorld:PersistentLevel.HoldingAreaDestination_1')
        if holding:
            holding.ExitPointsCounter = -99
        return True

    if disable_portal:
        RunHook("Engine.Actor.TriggerGlobalEventClass", 'SpeedrunPractice', disable_portal_hook)
    else:
        RemoveHook("Engine.Actor.TriggerGlobalEventClass", 'SpeedrunPractice')
