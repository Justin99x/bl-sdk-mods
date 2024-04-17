from Mods.WD.dumperdata import level_pkgs
from Mods.ModMenu.ModObjects import Game
from unrealsdk import FindObject, LoadObject, LoadPackage, Log

"""Use this script when an object doesn't load and you don't know the package. You need to 
know the map it loads on, and this will cycle through the available packages in that map 
based on dumperdata.py"""

Log(LoadObject('ItemPoolDefinition', 'GD_BigLoaderTurret.Weapons.BigLoaderTurret_Weapon'))

for package in level_pkgs[Game.BL2]['SandwormLair_P']:

    LoadPackage(package)

    obj = FindObject('ItemPoolListDefinition', 'GD_Anemone_ItemPools.ListDefs.RaidBossEnemyGunsAndGear')
    if obj:
        Log(f"Success! Package {package}")
        break
