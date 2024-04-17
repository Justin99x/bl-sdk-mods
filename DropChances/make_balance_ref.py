import inspect
import json
import os
from random import choice

from Mods.WD.drops import ItemType, Rarity, path_name, PC
from unrealsdk import Log, FindAll, FindObject, LogAllCalls, FStruct, UObject, GetEngine, LoadObject, LoadPackage, FArray


def get_weapon_data(balance, base_definition):
    part_list = balance.RuntimePartListCollection
    manufacturer_definition = base_definition.Manufacturers[0].Manufacturer
    weapon_type_definition = part_list.AssociatedWeaponType
    return weapon_type_definition, manufacturer_definition


def get_com_data(balance):
    b = balance
    while len(b.ClassModDefinitions) == 0:
        if b.BaseDefinition is None:
            return None
        b = b.BaseDefinition
    item_definition = choice(b.ClassModDefinitions)

    return item_definition, item_definition.ManufacturerOverride


def get_item_data(balance, base_definition):
    part_list = balance.PartListCollection
    if balance.Manufacturers is None:
        balance.DumpObject()
    if len(balance.Manufacturers) > 0:
        manufacturer_definition = choice(balance.Manufacturers).Manufacturer
    else:
        manufacturer_definition = choice(base_definition.Manufacturers).Manufacturer
    item_definition = balance.InventoryDefinition
    if item_definition is None:
        item_definition = part_list.AssociatedItem
        if item_definition is None:
            Log("No PartList.AssociatedItem and no InventoryDefinition")
            return None
    return item_definition, manufacturer_definition


def get_inv_from_balance(balance, game_stages: list):
    base_definition = balance
    while base_definition.BaseDefinition is not None:
        base_definition = base_definition.BaseDefinition
    if "WeaponBalanceDefinition" in balance.Class.Name:  # Also covers MissionWeaponBalanceDefinition
        inventory_definition, manufacturer = get_weapon_data(balance, base_definition)
    elif balance.Class.Name == "ClassModBalanceDefinition":
        inventory_definition, manufacturer = get_com_data(balance)
    else:
        inventory_definition, manufacturer = get_item_data(balance, base_definition)

    item = PC.Spawn(inventory_definition.InventoryClass)
    game_stage = choice(game_stages)
    item.Gamestage = game_stage
    item.InitializeInventory(balance, manufacturer, game_stage, None)
    return item


def get_item_type(item: UObject) -> ItemType:
    type_map = {
        'WillowShield': ItemType.Shield,
        'WillowClassMod': ItemType.ClassMod,
        'WillowGrenadeMod': ItemType.Grenade,
        'WillowUsableCustomizationItem': ItemType.Skin,
        'WillowArtifact': ItemType.Artifact,
    }
    if item.Class.Name == 'WillowWeapon':
        wt = item.DefinitionData.WeaponTypeDefinition.WeaponType
        return ItemType(wt)
    elif type_map.get(item.Class.Name):
        return type_map.get(item.Class.Name)
    else:
        return ItemType.Other


def get_item_rarity(rarity_level: int):
    if rarity_level == 0:
        return Rarity.Other
    if rarity_level in [1, 2, 3, 4]:
        return Rarity(rarity_level)
    if rarity_level in [5, 7, 8, 9, 10]:
        return Rarity.Legendary
    if rarity_level == 6:
        return Rarity.ETech
    if rarity_level == 500:
        return Rarity.Pearlescent
    if rarity_level == 501:
        return Rarity.Seraph
    if rarity_level == 506:
        return Rarity.Rainbow
    raise ValueError(f"Unknown rarity {rarity_level} provided")


def get_balance_to_rarity():
    '''One time run to build the balances.json file. Keeping here for reference'''
    inv_balances = FindAll('InventoryBalanceDefinition')
    weap_balances = FindAll('WeaponBalanceDefinition')
    cm_balances = FindAll('ClassModBalanceDefinition')
    item_balances = FindAll('ItemBalanceDefinition')
    mission_weap_balances = FindAll('MissionWeaponBalanceDefinition')

    all_balances = inv_balances[1:] + weap_balances[1:] + cm_balances[1:] + item_balances[1:] + mission_weap_balances[1:]

    balance_rarities = {}
    for inv_bal in all_balances:
        try:
            item = get_inv_from_balance(inv_bal, [80])
        except:
            Log(f"Failed to process {inv_bal}")
            continue
        item_type = get_item_type(item)
        if item_type == ItemType.Other:
            continue
        rarity = get_item_rarity(item.RarityLevel)
        if item_type == ItemType.Artifact:
            rarity = Rarity.Other
        balance_rarities[path_name(inv_bal)] = (rarity.value, item_type.value)

    path = 'Mods/WD/balances.json'
    with open(path, "w") as file:
        json.dump(balance_rarities, file, indent=4)


if __name__ == '__main__':
    get_balance_to_rarity()
