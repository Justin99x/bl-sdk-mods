from random import choice, choices
from typing import List, Tuple

import unrealsdk
from Mods.AnyPercentHelper.utilities import Utilities

SHOTGUNS = [
    ('Sanctuary', [8, 9, 10], True, 'Sanctuary'),
    ('Grass_B', [14, 15, 16], True, 'Overlook')
]

TURTLES = [
    ('IceCanyon', [6, 7, 8], True, 'Frostburn')
]

AMPS = [
    ('Outwash', [13, 14, 15], True, 'The Fridge'),
    ('Grass_C', [16, 17, 18], False, 'Hyperion Bridge'),
    ('PandoraPark', [17, 18, 19], False, 'WEP'),
    ('Cliffs', [18, 19, 20], False, 'Thousand Cuts')
]


class GearRandomizer:

    def __init__(self):
        self.PC = Utilities.get_current_player_controller()
        self.maps = self.PC.ActivatedTeleportersList
        self.level = self.PC.PlayerReplicationInfo.ExpLevel
        self.min_amp_damage = 100
        unrealsdk.LoadPackage("Sanctuary_P")  # Needed for maps that don't have gun vendors.
        health_flat_pool = unrealsdk.FindObject('ItemPoolDefinition',
                                                'GD_ItemPools_Shop.HealthShop.HealthShop_Items')
        health_featured_pool = unrealsdk.FindObject('ItemPoolDefinition',
                                                    'GD_ItemPools_Shop.HealthShop.HealthShop_FeaturedItem')
        shotgun_flat_pool = unrealsdk.FindObject('ItemPoolDefinition',
                                                 'GD_ItemPools_Shop.Items.Shoppool_Weapons_FlatChance')
        shotgun_featured_pool = unrealsdk.FindObject('ItemPoolDefinition',
                                                     'GD_ItemPools_Shop.WeaponPools.Shoppool_FeaturedItem_WeaponMachine')
        self.turtle_shield_kwargs = {
            "flat_pool": health_flat_pool,
            "featured_pool": health_featured_pool,
            "qualifying_func": self.is_white_turtle,
            "sort_func": lambda x: 1
        }
        self.amp_shield_kwargs = {
            "flat_pool": health_flat_pool,
            "featured_pool": health_featured_pool,
            "qualifying_func": self.is_good_amp,
            "sort_func": self.get_impact_damage
        }
        self.shotgun_kwargs = {
            "flat_pool": shotgun_flat_pool,
            "featured_pool": shotgun_featured_pool,
            "qualifying_func": self.is_jakobs_multi_barrel,
            "sort_func": self.get_impact_damage
        }

    def evaluate_probability(self, attrib_init_data: unrealsdk.FStruct):
        """Evaluate Probability (which is really a weight) from BalancedItems Array"""
        init_data_tuple = (attrib_init_data.BaseValueConstant, attrib_init_data.BaseValueAttribute,
                           attrib_init_data.InitializationDefinition, attrib_init_data.BaseValueScaleConstant)
        obj = unrealsdk.FindObject("AttributeInitializationDefinition",
                                   "Engine.Default__AttributeInitializationDefinition")
        return obj.EvaluateInitializationData(init_data_tuple, self.PC)

    def get_weapon_data(self, balance, base_definition):
        part_list = balance.RuntimePartListCollection
        manufacturer_definition = base_definition.Manufacturers[0].Manufacturer
        weapon_type_definition = part_list.AssociatedWeaponType
        return weapon_type_definition, manufacturer_definition

    def get_com_data(self, balance):
        b = balance
        while len(b.ClassModDefinitions) == 0:
            if b.BaseDefinition is None:
                return None
            b = b.BaseDefinition
        item_definition = choice(b.ClassModDefinitions)

        return item_definition, item_definition.ManufacturerOverride

    def get_item_data(self, balance, base_definition):
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
                unrealsdk.Log("No PartList.AssociatedItem and no InventoryDefinition")
                return None
        return item_definition, manufacturer_definition

    def get_item_from_balance(self, balance, game_stages: list):
        base_definition = balance
        while base_definition.BaseDefinition is not None:
            base_definition = base_definition.BaseDefinition
        if balance.Class.Name == "WeaponBalanceDefinition":
            inventory_definition, manufacturer = self.get_weapon_data(balance, base_definition)
        elif balance.Class.Name == "ClassModBalanceDefinition":
            inventory_definition, manufacturer = self.get_com_data(balance)
        else:
            inventory_definition, manufacturer = self.get_item_data(balance, base_definition)

        item = self.PC.Spawn(inventory_definition.InventoryClass)
        game_stage = choice(game_stages)
        item.Gamestage = game_stage
        item.InitializeInventory(balance, manufacturer, game_stage, None)
        return item

    def get_item_from_pool(self, pool, game_stages: list):
        if pool.MinGameStageRequirement is not None:
            pool_stage_req = pool.MinGameStageRequirement.GetValue(self.PC)[0]
        else:
            pool_stage_req = 0
        if pool_stage_req > max(game_stages):  # Basically perform a re-roll since we picked an unavailable type
            return None
        game_stages = [stage for stage in game_stages if stage >= pool_stage_req]
        choice_obj = choices(
            [item.ItmPoolDefinition if item.InvBalanceDefinition is None else item.InvBalanceDefinition for item in
             pool.BalancedItems],
            [self.evaluate_probability(item.Probability) for item in pool.BalancedItems]
        )[0]
        if choice_obj.Class.Name in ["ItemPoolDefinition", "KeyedItemPoolDefinition"]:
            return self.get_item_from_pool(choice_obj, game_stages)  # Recursion!
        else:
            return self.get_item_from_balance(choice_obj, game_stages)

    def get_items_from_pool(self, pool, quantity: int, game_stages: list):
        items = []
        while len(items) < quantity:
            item = self.get_item_from_pool(pool, game_stages)
            if item:
                items.append(item)
        return items

    def is_jakobs_multi_barrel(self, weapon):
        if weapon.Class.Name != 'WillowWeapon':
            return False
        barrels = ['SG_Barrel_Bandit', 'SG_Barrel_Jakobs', 'SG_Barrel_Torgue']
        return weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun' and weapon.DefinitionData.BarrelPartDefinition.Name in barrels

    def get_total_damage(self, weapon):
        projectiles_attr = unrealsdk.FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponProjectilesPerShot")
        projectiles = projectiles_attr.GetValue(weapon)[0]
        return weapon.GetMultiProjectileDamage() * projectiles

    def is_white_turtle(self, item):
        return item.Class.Name == 'WillowShield' and item.DefinitionData.BalanceDefinition.Name == 'ItemGrade_Gear_Shield_Juggernaut_01_Common'

    def get_impact_damage(self, item):
        impact_damage_attr = unrealsdk.FindObject("AttributeDefinition", "D_Attributes.Shield.ImpactShield_DamageBonus")
        return impact_damage_attr.GetValue(item)[0]

    def is_good_amp(self, item):
        amp_damage = self.get_impact_damage(item)
        if item.Class.Name != 'WillowShield' or item.DefinitionData.ManufacturerDefinition.Name != 'Hyperion' or amp_damage < self.min_amp_damage:
            return False
        self.min_amp_damage = amp_damage + 25
        if amp_damage >= 175:
            self.min_amp_damage = 1000  # Essentially means don't check future vendors
        return True

    def get_inventory_from_vendor(self, game_stages: list, farm: bool, flat_pool, featured_pool, qualifying_func,
                                  sort_func):
        items = self.get_items_from_pool(flat_pool, 7, game_stages) + self.get_items_from_pool(featured_pool, 1,
                                                                                               game_stages)
        qualifying_items = [item for item in items if qualifying_func(item)]
        if len(qualifying_items) > 0:
            return max(qualifying_items, key=sort_func)
        if farm:
            return self.get_inventory_from_vendor(game_stages, farm, flat_pool, featured_pool, qualifying_func,
                                                  sort_func)
        return None

    def get_game_stage(self, item):
        return item.DefinitionData.GameStage

    def filter_gear(self, items):
        item_to_equip = max([item for item in items if self.get_game_stage(item) <= self.level],
                            key=self.get_game_stage)
        overlevel_items = [item for item in items if self.get_game_stage(item) > self.level]
        return item_to_equip, overlevel_items

    def filter_gear(self, items_msgs: Tuple[List, List]) -> Tuple[Tuple, List[Tuple]]:

        usable_items = [(item, msg) for item, msg in items_msgs if self.get_game_stage(item) <= self.level]
        overlevel_items = [(item, msg) for item, msg in items_msgs if self.get_game_stage(item) > self.level]

        item_to_equip = max(usable_items, key=lambda x: self.get_game_stage(x[0]))

        # Log to console
        unrealsdk.Log(item_to_equip[1])
        for item in overlevel_items:
            unrealsdk.Log(item[1])
        return item_to_equip[0], [item[0] for item in overlevel_items]

    def cycle_vendors(self, vendors, kwargs):
        rarity = {1: 'White', 2: 'Green', 3: 'Blue', 4: 'Purple', 5: 'Orange'}
        items = []
        msgs = []
        for vendor in vendors:
            if vendor[0] in self.maps:
                item = self.get_inventory_from_vendor(vendor[1], vendor[2], **kwargs)
                if item:
                    items.append(item)
                    msgs.append(
                        f'{rarity.get(item.GetRarityLevel(), "Unknown")} Level {item.GetGameStage()} {item.GetShortHumanReadableName()} from vendor in {vendor[3]}')
        return list(zip(items, msgs))

    def throw_old_gear(self):
        inventory_manager = self.PC.GetPawnInventoryManager()
        all_weapons = unrealsdk.FindAll('WillowWeapon')
        for weapon in all_weapons:
            if weapon.Owner == self.PC.pawn and self.is_jakobs_multi_barrel(weapon):
                if weapon in inventory_manager.GetEquippedWeapons():
                    self.PC.pawn.TossInventory(weapon)
                else:
                    inventory_manager.ThrowBackpackInventory(
                        weapon)  # TossInventory sometimes dupes backpack weapons, have to use this
        all_shields = unrealsdk.FindAll('WillowShield')
        for shield in all_shields:
            if shield.Owner == self.PC.pawn and \
                    shield.DefinitionData.ManufacturerDefinition.Name in ['Pangolin', 'Hyperion']:
                self.PC.pawn.TossInventory(shield)

    def randomize_gear(self):
        try:
            holding_shotgun = (self.PC.pawn.Weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun')
        except:
            holding_shotgun = False

        shotguns = self.cycle_vendors(SHOTGUNS, self.shotgun_kwargs)
        turtles = self.cycle_vendors(TURTLES, self.turtle_shield_kwargs)
        amps = self.cycle_vendors(AMPS, self.amp_shield_kwargs)

        self.throw_old_gear()
        unrealsdk.Log("Checking vendors for gear!")

        equip_shotgun, overlevel_shotguns = self.filter_gear(shotguns)
        equip_shield, overlevel_shields = self.filter_gear(turtles + amps)

        inv_manager = self.PC.GetPawnInventoryManager()
        inv_manager.AddInventory(equip_shotgun, holding_shotgun)
        inv_manager.AddInventory(equip_shield, True)
        for sg in overlevel_shotguns:
            inv_manager.AddInventory(sg, False)
        for sh in overlevel_shields:
            inv_manager.AddInventory(sh, False)

        Utilities.feedback(f"Guns and shields randomized! Check console for details.")
