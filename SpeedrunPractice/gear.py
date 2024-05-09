from random import choice, choices
from typing import List, Optional, Tuple

from Mods.SpeedrunPractice.utilities import feedback, get_current_player_controller
from unrealsdk import FStruct, FindAll, FindObject, LoadPackage, Log, RemoveHook, RunHook, UObject

SHOTGUNS = [
    ('Sanctuary', 10, True, 'Sanctuary'),
    ('Grass_B', 16, True, 'Overlook')
]

TURTLES = [
    ('IceCanyon', 8, True, 'Frostburn')
]

AMPS = [
    ('Outwash', 15, True, 'The Fridge'),
    ('Grass_C', 18, False, 'Hyperion Bridge'),
    ('PandoraPark', 19, False, 'WEP'),
    ('Cliffs', 20, False, 'Thousand Cuts')
]


class GearRandomizer:

    def __init__(self):
        self.PC = get_current_player_controller()
        self.maps = self.PC.ActivatedTeleportersList
        self.level = self.PC.PlayerReplicationInfo.ExpLevel
        self.min_amp_damage = 100
        LoadPackage("Sanctuary_P")  # Needed for maps that don't have gun vendors.
        health_flat_pool = FindObject('ItemPoolDefinition',
                                      'GD_ItemPools_Shop.HealthShop.HealthShop_Items')
        health_featured_pool = FindObject('ItemPoolDefinition',
                                          'GD_ItemPools_Shop.HealthShop.HealthShop_FeaturedItem')
        shotgun_flat_pool = FindObject('ItemPoolDefinition',
                                       'GD_ItemPools_Shop.Items.Shoppool_Weapons_FlatChance')
        shotgun_featured_pool = FindObject('ItemPoolDefinition',
                                           'GD_ItemPools_Shop.WeaponPools.Shoppool_FeaturedItem_WeaponMachine')
        self.sanctuary_shotgun_pool = FindObject('ItemPoolDefinition',
                                                 'GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_02_Uncommon')
        self.game_stage_variance = FindObject('AttributeInitializationDefinition',
                                              'GD_Economy.VendingMachine.Init_VendingMachine_LootGamestageVariance')

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
            "sort_func": self.get_total_damage
        }

    def get_items_from_pool(self, pool: UObject, game_stage: int, game_stage_variance_def: Optional[UObject] = None) -> List[UObject]:
        '''Spawn inventory from any ItemPoolDefinition'''
        default_item_pool = FindObject('ItemPool', 'WillowGame.Default__ItemPool')
        spawned_items = []

        def append_inv(caller, function, params):
            spawned_items.append(caller)
            return True

        RunHook("WillowGame.WillowItem.OnCreate", "Dev", append_inv)
        RunHook("WillowGame.WillowWeapon.OnCreate", "Dev", append_inv)
        default_item_pool.SpawnBalancedInventoryFromPool(pool, game_stage, game_stage, self.PC, [], game_stage_variance_def)
        RemoveHook("WillowGame.WillowItem.OnCreate", "Dev")
        RemoveHook("WillowGame.WillowWeapon.OnCreate", "Dev")

        return spawned_items

    def is_jakobs_multi_barrel(self, weapon):
        if weapon.Class.Name != 'WillowWeapon':
            return False
        barrels = ['SG_Barrel_Bandit', 'SG_Barrel_Jakobs', 'SG_Barrel_Torgue']
        return weapon.DefinitionData.WeaponTypeDefinition.Name == 'WT_Jakobs_Shotgun' and weapon.DefinitionData.BarrelPartDefinition.Name in barrels

    def is_probably_sanctuary_shotgun(self, weapon):
        return weapon.DefinitionData.WeaponTypeDefinition.WeaponType == 1 and weapon.DefinitionData.GameStage == 6

    def get_total_damage(self, weapon):
        projectiles_attr = FindObject("AttributeDefinition", "D_Attributes.Weapon.WeaponProjectilesPerShot")
        projectiles = projectiles_attr.GetValue(weapon)[0]
        return weapon.GetMultiProjectileDamage() * projectiles

    def is_white_turtle(self, item):
        return item.Class.Name == 'WillowShield' and item.DefinitionData.BalanceDefinition.Name == 'ItemGrade_Gear_Shield_Juggernaut_01_Common'

    def get_impact_damage(self, item):
        impact_damage_attr = FindObject("AttributeDefinition", "D_Attributes.Shield.ImpactShield_DamageBonus")
        return impact_damage_attr.GetValue(item)[0]

    def is_good_amp(self, item):
        amp_damage = self.get_impact_damage(item)
        if item.Class.Name != 'WillowShield' or item.DefinitionData.ManufacturerDefinition.Name != 'Hyperion' or amp_damage < self.min_amp_damage:
            return False
        self.min_amp_damage = amp_damage + 25
        if amp_damage >= 175:
            self.min_amp_damage = 1000  # Essentially means don't check future vendors
        return True

    def get_inventory_from_vendor(self, game_stage: int, farm: bool, flat_pool, featured_pool, qualifying_func, sort_func):
        items = self.get_items_from_pool(flat_pool, game_stage, self.game_stage_variance) + \
                self.get_items_from_pool(featured_pool, game_stage, self.game_stage_variance)
        qualifying_items = [item for item in items if qualifying_func(item)]
        if len(qualifying_items) > 0:
            return max(qualifying_items, key=sort_func)
        if farm:
            return self.get_inventory_from_vendor(game_stage, farm, flat_pool, featured_pool, qualifying_func, sort_func)
        return None

    def get_game_stage(self, item):
        return item.DefinitionData.GameStage

    def filter_gear(self, items_msgs: List[Tuple]) -> Tuple:

        usable_items = [(item, msg) for item, msg in items_msgs if self.get_game_stage(item) <= self.level]
        overlevel_items = [(item, msg) for item, msg in items_msgs if self.get_game_stage(item) > self.level]

        item_to_equip = (None, '')
        if usable_items:
            item_to_equip = max(usable_items, key=lambda x: self.get_game_stage(x[0]))

        # Log to console
        Log(item_to_equip[1])
        for item in overlevel_items:
            Log(item[1])
        return item_to_equip[0], [item[0] for item in overlevel_items]

    def cycle_vendors(self, vendors, kwargs):
        rarity = {1: 'White', 2: 'Green', 3: 'Blue', 4: 'Purple', 5: 'Orange'}
        items = []
        msgs = []
        for vendor in vendors:
            if vendor[0] in self.maps and not (vendor[0] == 'Sanctuary' and self.level < 10):
                item = self.get_inventory_from_vendor(vendor[1], vendor[2], **kwargs)
                if item:
                    items.append(item)
                    msgs.append(
                        f'{rarity.get(item.GetRarityLevel(), "Unknown")} Level {item.GetGameStage()} {item.GetShortHumanReadableName()} from vendor in {vendor[3]}')
        return list(zip(items, msgs))

    def get_sanctuary_shotgun(self):
        shotgun = []
        msg = []
        if self.PC.GetActivePlotCriticalMissionNumber() >= 5:
            shotgun = self.get_items_from_pool(self.sanctuary_shotgun_pool, 6)
            msg = f'Green Level 6 {shotgun[0].GetShortHumanReadableName()} from Sanctuary mission turn in'
        return list(zip(shotgun, [msg]))

    def throw_old_gear(self):
        inventory_manager = self.PC.GetPawnInventoryManager()
        all_weapons = FindAll('WillowWeapon')
        for weapon in all_weapons:
            if weapon.Owner == self.PC.pawn and (self.is_jakobs_multi_barrel(weapon) or self.is_probably_sanctuary_shotgun(weapon)):
                if weapon in inventory_manager.GetEquippedWeapons():
                    self.PC.pawn.TossInventory(weapon)
                else:
                    inventory_manager.ThrowBackpackInventory(
                        weapon)  # TossInventory sometimes dupes backpack weapons, have to use this
        all_shields = FindAll('WillowShield')
        for shield in all_shields:
            if shield.Owner == self.PC.pawn and \
                    shield.DefinitionData.ManufacturerDefinition.Name in ['Pangolin', 'Hyperion']:
                self.PC.pawn.TossInventory(shield)

    def randomize_gear(self):
        try:
            holding_shotgun = (self.PC.pawn.Weapon.DefinitionData.WeaponTypeDefinition.WeaponType == 1)
        except:
            holding_shotgun = False

        shotguns = self.cycle_vendors(SHOTGUNS, self.shotgun_kwargs) + self.get_sanctuary_shotgun()
        turtles = self.cycle_vendors(TURTLES, self.turtle_shield_kwargs)
        amps = self.cycle_vendors(AMPS, self.amp_shield_kwargs)

        self.throw_old_gear()
        Log("Checking vendors for gear!")

        equip_shotgun, overlevel_shotguns = self.filter_gear(shotguns)
        equip_shield, overlevel_shields = self.filter_gear(turtles + amps)

        inv_manager = self.PC.GetPawnInventoryManager()
        if equip_shotgun:
            inv_manager.AddInventory(equip_shotgun, holding_shotgun)
        if equip_shield:
            inv_manager.AddInventory(equip_shield, True)
        for sg in overlevel_shotguns:
            inv_manager.AddInventory(sg, False)
        for sh in overlevel_shields:
            inv_manager.AddInventory(sh, False)

        feedback(self.PC, f"Guns and shields randomized! Check console for details.")
