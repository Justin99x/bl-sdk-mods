import unrealsdk
from Mods import ModMenu


class DisableAchievements(ModMenu.SDKMod):
    Name: str = "Disable Achievements"
    Author: str = "Justin99"
    Description: str = "Disables the Achivements option in the in-game menu to prevent Steam from popping up and stealing focus."
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    @ModMenu.Hook('OnlineSubsystemSteamworks.OnlineSubsystemSteamworks.ShowAchievementsUI')
    def block_achievements(self, caller, function, params) -> bool:
        return False

    def Enable(self) -> None:
        super().Enable()

    def Disable(self) -> None:
        super().Disable()


instance = DisableAchievements()

if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break

ModMenu.RegisterMod(instance)
