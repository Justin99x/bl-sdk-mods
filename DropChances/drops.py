"""
    Can I create an object that handles all possibilities?
        Mutually exclusive or independent
        Loot pool or loot pool list
        item pool or balanced item
        cumulative probability - track through item pools too?
        evaluated probability vs attributeinitializationdata
        is it a dataclass?
        avoid unreal objects outside of string names?

    Object types to cover
    ItemPoolListDefinition - carries ItemPoolInfos and ItemPoolListDefinitions
    ItemPoolInfo - carries ItemPoolDefinition and AttributeInitialization
    InteractiveObjectLootListDefinition - carries LootConfigurationDatas
    LootConfigurationData - carries LootAttachmentDatas and AttributeInitializationData
    LootAttachementData - carries



    Enemy Source
        - Keep interface of needing to provide pools and pool lists. Need control over excluding dedicated drop sources

    IO Source
        - Need pools and pool lists, but pool lists can be mutually exclusive
        - Pool list could get treated like an item pool, but then multiple things under
        - Mutually exclusive flag?

    """
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from unrealsdk import FindObject, GetEngine, LoadPackage, Log, UClass, UObject


class ItemType(Enum):
    """Weapon numbers are important - match with UnrealScript Enum"""
    Pistol = 0
    Shotgun = 1
    SMG = 2
    SniperRifle = 3
    AssaultRifle = 4
    RocketLauncher = 5
    ClassMod = 6
    Grenade = 7
    Shield = 8
    Artifact = 9
    Skin = 10
    Other = 11

    def __init__(self, _):
        if self.value <= 5:
            self.category = 'Weapon'
        elif 6 <= self.value <= 9:
            self.category = 'Item'
        else:
            self.category = 'Other'


class Rarity(Enum):
    """Numbers match in game values except there's a bunch more legendary numbers that are handled manually in methods below."""
    Other = 0
    White = 1
    Green = 2
    Blue = 3
    Purple = 4
    ETech = 5
    Legendary = 6
    Pearlescent = 7
    Seraph = 8
    Rainbow = 9

    def __init__(self, _):
        if self.value <= 5:
            self.category = 'NonUnique'
        else:
            self.category = 'Legendary+'


@dataclass
class InventoryBalanceDefinition:
    pass


class AttributeDefinition:
    def GetValue(self, Object: UObject) -> Tuple[float, Any]:
        pass


@dataclass
class BalanceFormula:
    bEnabled: bool
    Multiplier: 'AttributeInitializationData'
    Level: 'AttributeInitializationData'
    Power: 'AttributeInitializationData'
    Offset: 'AttributeInitializationData'


@dataclass
class AttributeInitializationDefinition:
    ValueFormula: BalanceFormula


@dataclass
class AttributeInitializationData:
    BaseValueConstant: float
    BaseValueAttribute: AttributeDefinition
    InitializationDefinition: AttributeInitializationDefinition
    BaseValueScaleConstant: float


@dataclass
class BalancedInventoryData:
    ItmPoolDefinition: 'ItemPoolDefinition'
    InvBalanceDefinition: InventoryBalanceDefinition
    Probability: AttributeInitializationData
    bDropOnDeath: bool


@dataclass
class ItemPoolDefinition:
    BalancedItems: List[BalancedInventoryData]
    Quantity: AttributeInitializationData
    MinGameStageRequirement: AttributeDefinition
    MinGameStageRequirement: AttributeDefinition
    bEligibleForUncommonWeightMultiplier: bool


@dataclass
class ItemPoolDefinitionWrapper:
    item_pool_definition: ItemPoolDefinition
    probability: Fraction
    cumulative_probability: Fraction
    parents: List['ItemPoolDefinitionWrapper']


@dataclass
class InventoryBalanceDefinitionWrapper:
    inventory_balance_definition: InventoryBalanceDefinition
    probability: Fraction
    cumulative_probability: Fraction
    parents: List[ItemPoolDefinitionWrapper]
    rarity: Rarity
    item_type: ItemType


@dataclass
class ItemPoolInfoPathArgs:
    item_pool_path: str
    BVC: float
    BVA_path: Optional[str]
    ID_path: Optional[str]
    BVSC: float


@dataclass
class ItemPoolInfo:
    ItemPool: ItemPoolDefinition
    PoolProbability: AttributeInitializationData

    @classmethod
    def from_paths(cls, args: ItemPoolInfoPathArgs):
        item_pool = cast(ItemPoolDefinition, FindObject('ItemPoolDefinition', args.item_pool_path))
        BVA = None
        if args.BVA_path:
            BVA = cast(AttributeDefinition, FindObject('AttributeDefinition', args.BVA_path))
            if not BVA:
                ValueError(f"Could not find object with path {args.BVA_path}")
        ID = None
        if args.ID_path:
            ID = cast(AttributeInitializationDefinition, FindObject('AttributeInitializationDefinition', args.ID_path))
            if not ID:
                ValueError(f"Could not find object with path {args.ID_path}")

        pool_probability = AttributeInitializationData(args.BVC, BVA, ID, args.BVSC)
        return ItemPoolInfo(item_pool, pool_probability)


@dataclass
class LootConfigurationData:
    ConfigurationName: str
    Weight: AttributeInitializationData
    ItemAttachments: List[ItemPoolInfo]


@dataclass
class InteractiveObjectLootListDefinition:
    LootData: List[LootConfigurationData]


@dataclass
class InteractiveObjectBalanceDefinition:
    DefaultIncludedLootLists: List[InteractiveObjectLootListDefinition]
    DefaultLoot: List[LootConfigurationData]


@dataclass
class ItemPoolListDefinition:
    ItemPoolIncludedLists: List['ItemPoolListDefinition']
    ItemPools: List[ItemPoolInfo]

    @classmethod
    def from_paths(cls, ipld_paths: List[str], ipi_args_list: List[ItemPoolInfoPathArgs]):
        item_pool_included_lists = [cast(ItemPoolListDefinition, FindObject('ItemPoolListDefinition', path)) for path in ipld_paths]
        item_pools = [ItemPoolInfo.from_paths(ipi_arg) for ipi_arg in ipi_args_list]
        return ItemPoolListDefinition(item_pool_included_lists, item_pools)


@dataclass
class AIPawnPlaythroughData:
    PlayThrough: int
    CustomItemPoolIncludedLists: List[ItemPoolListDefinition]
    CustomItemPoolList: List[ItemPoolInfo]


@dataclass
class AIPawnBalanceDefinition:
    PlayThroughs: List[AIPawnPlaythroughData]
    DefaultItemPoolIncludedLists: List[ItemPoolListDefinition]
    DefaultItemPoolList: List[ItemPoolInfo]


def path_name(obj):
    return UClass.PathName(obj)


def eval_init_data(attrib_init_data: AttributeInitializationData):
    init_data_tuple = (attrib_init_data.BaseValueConstant, attrib_init_data.BaseValueAttribute,
                       attrib_init_data.InitializationDefinition, attrib_init_data.BaseValueScaleConstant)

    obj = FindObject("AttributeInitializationDefinition", "Engine.Default__AttributeInitializationDefinition")
    prob = obj.EvaluateInitializationData(init_data_tuple, _PC)
    if prob == 0:
        try:
            prob = attrib_init_data.InitializationDefinition.ValueFormula.Level.BaseValueAttribute.GetValue(_PC)[0] \
                   * attrib_init_data.BaseValueScaleConstant
        except AttributeError:
            pass
    return Fraction.from_float(prob).limit_denominator(10000)


def eval_prob_balanced_item(balanced_item: BalancedInventoryData, elig_uncommon_weight: bool):
    """Have to do recursive here to find out if any subpools have 0 probability, which changes weights at the higher level."""
    if not balanced_item.bDropOnDeath:
        return Fraction(0)

    if balanced_item.ItmPoolDefinition:
        item_pool_def = balanced_item.ItmPoolDefinition
        if item_pool_def.MinGameStageRequirement and _GAME_STAGE < item_pool_def.MinGameStageRequirement.GetValue(_PC)[0]:
            return Fraction(0)
        if sum([eval_prob_balanced_item(balanced_item, elig_uncommon_weight)
             for balanced_item in balanced_item.ItmPoolDefinition.BalancedItems], Fraction(0)) == 0:
            return Fraction(0)

    probability = eval_init_data(balanced_item.Probability)

    if elig_uncommon_weight and path_name(balanced_item.Probability.InitializationDefinition) == 'GD_Balance.Weighting.Weight_2_Uncommon':
        probability = probability * _UNCOMMON_WEIGHT_MULT

    return probability


def eval_prob_item_pool_info(item_pool_info: ItemPoolInfo):

    probability = eval_init_data(item_pool_info.PoolProbability)
    if item_pool_info.ItemPool:
        item_pool_def = item_pool_info.ItemPool
        if item_pool_def.MinGameStageRequirement and _GAME_STAGE < item_pool_def.MinGameStageRequirement.GetValue(_PC)[0]:
            probability = Fraction(0)
    return probability


class LootSource:
    """Loot source must represent a series of independent loot pools.
    Chest configurations need to be their own loot sources, aggregated later"""

    def __init__(self, name: str, pool_list: List[ItemPoolInfo]):
        self.name = name
        self.pool_list = pool_list

        # TODO: Retain extra info about the source. Currently only have pool list and final result.
        # TODO: Could wrap ItemPoolInfo to add the additional stuff
        self.success_dist = self.dist_from_pool_list()

    @classmethod
    def item_pools_from_item_pool_list_def(cls, item_pool_list_def: ItemPoolListDefinition) -> List[ItemPoolInfo]:
        item_pools = []
        for pool in item_pool_list_def.ItemPools:
            item_pools += [pool]
        for item_pool_list_def in item_pool_list_def.ItemPoolIncludedLists:
            item_pools.extend(cls.item_pools_from_item_pool_list_def(item_pool_list_def))
        return item_pools

    @classmethod
    def inv_balances_from_pool(cls, in_item_pool: ItemPoolDefinitionWrapper) -> List[InventoryBalanceDefinitionWrapper]:
        """Recursive function to get all terminal inventory balances along with their probability of rolling from a given pool"""
        elig_uncommon_weight = in_item_pool.item_pool_definition.bEligibleForUncommonWeightMultiplier
        total_weight = sum([eval_prob_balanced_item(balanced_item, elig_uncommon_weight)
                            for balanced_item in in_item_pool.item_pool_definition.BalancedItems], Fraction(0))
        inv_balance_defs: List[InventoryBalanceDefinitionWrapper] = []

        for balanced_item in in_item_pool.item_pool_definition.BalancedItems:
            weight = eval_prob_balanced_item(balanced_item, elig_uncommon_weight)
            probability = 0 if total_weight == 0 else weight / total_weight
            cumulative_probability = in_item_pool.cumulative_probability * probability
            if cumulative_probability == 0:
                continue  # No sense continuing with zero probability

            if balanced_item.ItmPoolDefinition:
                item_pool = ItemPoolDefinitionWrapper(
                    item_pool_definition=balanced_item.ItmPoolDefinition,
                    probability=probability,
                    cumulative_probability=cumulative_probability,
                    parents=in_item_pool.parents + [in_item_pool]
                )
                inv_balance_defs += cls.inv_balances_from_pool(item_pool)

            elif balanced_item.InvBalanceDefinition:
                rarity_item_type = _BALANCE_REF.get(path_name(balanced_item.InvBalanceDefinition))
                if not rarity_item_type:
                    rarity_item_type = [0, 11]
                rarity = Rarity(rarity_item_type[0])
                item_type = ItemType(rarity_item_type[1])

                inv_bal_def = InventoryBalanceDefinitionWrapper(
                    inventory_balance_definition=balanced_item.InvBalanceDefinition,
                    probability=probability,
                    cumulative_probability=cumulative_probability,
                    parents=in_item_pool.parents + [in_item_pool],
                    rarity=rarity,
                    item_type=item_type
                )
                inv_balance_defs += [inv_bal_def]
        return inv_balance_defs

    @classmethod
    def k_successes(cls, probs: List[Fraction]) -> List[Fraction]:
        if len(probs) < 4:
            probs = probs + [Fraction(0)] * (4 - len(probs))
        n = len(probs)
        dp = [[Fraction(0) for _ in range(n + 1)] for __ in range(n + 1)]
        dp[0][0] = Fraction(1)

        for trials in range(1, n + 1):
            dp[trials][0] = (dp[trials - 1][0] * (1 - probs[trials - 1])).limit_denominator(1000000000)
            for successes in range(1, n + 1):
                dp[trials][successes] = (dp[trials - 1][successes] * (1 - probs[trials - 1]) + dp[trials - 1][successes - 1] * probs[
                    trials - 1]).limit_denominator(1000000000)

        success_list = [dp[n][k] for k in range(0, n + 1)]

        four_plus = sum(success_list[4:], Fraction(0))
        success_list = success_list[:4] + [four_plus]

        assert abs(sum(success_list, Fraction(0)).limit_denominator(1000000000) - Fraction(1)) < .00001
        return success_list

    def dist_from_pool_list(self) -> List[Fraction]:

        success_probs_by_pool: List[Fraction] = []
        for pool in self.pool_list:
            probability = eval_prob_item_pool_info(pool)
            item_pool_def_wrap = ItemPoolDefinitionWrapper(
                item_pool_definition=pool.ItemPool,
                probability=probability,
                cumulative_probability=probability,
                parents=[]
            )
            inv_balance_defs = self.inv_balances_from_pool(item_pool_def_wrap)
            cum_sum = sum([inv_bal.cumulative_probability for inv_bal in inv_balance_defs], Fraction(0))
            assert abs(cum_sum - probability) < 0.0001 or cum_sum == 0
            success_probs_by_pool += [sum([inv_bal.cumulative_probability for inv_bal in inv_balance_defs
                                           if _SUCCESS_DEF(inv_bal)], Fraction(0))]

        success_probs_by_pool = [p for p in success_probs_by_pool if p > 0]
        return self.k_successes(success_probs_by_pool)


class ItemPoolListSource(LootSource):
    """For instantiating from a set of path names for ItemPoolListDefinition"""

    def __init__(self, name: str, ipld_path_names: List[str]):
        pool_list: List[ItemPoolInfo] = []
        for ipld_path in ipld_path_names:
            ipld = cast(ItemPoolListDefinition, FindObject('ItemPoolListDefinition', ipld_path))
            pool_list.extend(self.item_pools_from_item_pool_list_def(ipld))

        super().__init__(name, pool_list)


class CustomItemPoolListSource(LootSource):
    """For instantiating from a custom ListDef - useful for recreating a pawn balance that has its DefaultItemPoolList defined"""

    def __init__(self, name: str, ipi_args_list: List[ItemPoolInfoPathArgs], ipld_path_names: List[str]):
        pool_list: List[ItemPoolInfo] = []

        for ipi_args in ipi_args_list:
            pool_list += [ItemPoolInfo.from_paths(ipi_args)]

        for ipld_path in ipld_path_names:
            ipld = cast(ItemPoolListDefinition, FindObject('ItemPoolListDefinition', ipld_path))
            pool_list.extend(self.item_pools_from_item_pool_list_def(ipld))

        super().__init__(name, pool_list)


class InteractiveObjectSource:
    """IO loot lists have separate configurations that are mutually exclusive. New base class that will create multiple LootSource
    instances and aggregate their results."""

    # TODO: Opening chests must check to make sure game stage requirements are met for all attachment points. New config chosen if not.
    def __init__(self, name: str, loot_configs: List[LootConfigurationData]):
        self.name = name
        self.configuration_sources: List[Tuple[LootSource, Fraction]] = []  # To keep track of probability of each config
        total_weight = sum([eval_init_data(lc.Weight) for lc in loot_configs], Fraction(0))
        for loot_config in loot_configs:
            probability = 0 if total_weight == 0 else eval_init_data(loot_config.Weight) / total_weight
            config_source = LootSource(loot_config.ConfigurationName, loot_config.ItemAttachments)
            self.configuration_sources += [(config_source, probability)]

        assert sum([cs[1] for cs in self.configuration_sources]) == 1
        self.success_dist: List[Fraction] = [Fraction(0)] * 5

        for i in range(5):
            self.success_dist[i] = sum([cs[0].success_dist[i] * cs[1] for cs in self.configuration_sources], Fraction(0))


class InteractiveObjectLootListSource(InteractiveObjectSource):
    """For instantiating from InteractiveObjectLootListDefinition paths"""

    def __init__(self, name: str, loot_list_def_paths: List[str]):
        loot_configs: List[LootConfigurationData] = []
        for path in loot_list_def_paths:
            loot_list_def = FindObject('InteractiveObjectLootListDefinition', path)
            loot_configs += list(loot_list_def.LootData)

        super().__init__(name, loot_configs)


class InteractiveObjectBalanceSource(InteractiveObjectSource):
    """For instantiating from a single path name for InteractiveObjectBalanceDefinition."""

    def __init__(self, name: str, iobd_path: str):
        iobd = cast(InteractiveObjectBalanceDefinition, FindObject('InteractiveObjectBalanceDefinition', iobd_path))
        loot_configs: List[LootConfigurationData] = list(iobd.DefaultLoot)
        for loot_list in iobd.DefaultIncludedLootLists:
            loot_configs += list(loot_list.LootData)

        super().__init__(name, loot_configs)


def copy_clipboard(inlist: List[List]) -> None:
    clipboard_string = ''
    for l in inlist:
        l = [str(i) for i in l]
        clipboard_string += '\t'.join(l) + '\n'

    subprocess.run(['powershell', '-command', f"Set-Clipboard -Value '{clipboard_string}'"])


if __name__ == '__main__':
    """User inputs"""
    _BALANCE_REF_PATH = 'Mods/WD/balances.json'
    # _SUCCESS_DEF: Callable[[InventoryBalanceDefinitionWrapper], bool] = lambda inv_bal: inv_bal.rarity == Rarity.Legendary and inv_bal.item_type == ItemType.ClassMod
    _SUCCESS_DEF: Callable[[InventoryBalanceDefinitionWrapper], bool] = lambda \
            inv_bal: inv_bal.rarity.category == 'Legendary+' and inv_bal.item_type.category != 'Other'


    with open(_BALANCE_REF_PATH, "r") as file:
        _BALANCE_REF = json.load(file)
    _PC = cast(UObject, GetEngine().GamePlayers[0].Actor)
    _GAME_STAGE = _PC.Pawn.GetGameStage()
    _BALANCE_MOD_P3 = FindObject('BalanceModifierDefinition', 'GD_Playthrough3Tuning.Balance.BalanceMod_PT3')
    _UNCOMMON_WEIGHT_MULT = Fraction(_BALANCE_MOD_P3.GetUncommonChestItemPoolWeightMultiplier(_GAME_STAGE)).limit_denominator(1000000)

    LoadPackage('Xmas_Dynamic')
    LoadPackage('Helios_UranusArena')
    LoadPackage('Ice_Dynamic')

    sources = [
        ItemPoolListSource('Badass Enemy Pool List', ['GD_Itempools.ListDefs.BadassEnemyGunsAndGear']),
        ItemPoolListSource('Chubby Pool List', ['GD_Itempools.ListDefs.ChubbyEnemyGunsAndGear']),
        ItemPoolListSource('Loot Midget Pool List', ['GD_Itempools.ListDefs.LootMidgetLoot']),
        ItemPoolListSource('Raid Boss Pool List', ['GD_Itempools.ListDefs.RaidBossEnemyGunsAndGear']),
        ItemPoolListSource('Standard Enemy Pool List', ['GD_Itempools.ListDefs.StandardEnemyGunsAndGear']),
        ItemPoolListSource('Super Badass Enemy Pool List', ['GD_Itempools.ListDefs.SuperBadassEnemyGunsAndGear']),
        ItemPoolListSource('Ultimate Badass Enemy Pool List', ['GD_Itempools.ListDefs.UltimateBadassEnemyGunsAndGear']),

        # InteractiveObjectLootListSource('Epic Chest Bandit', ['GD_Itempools.ListDefs.EpicChestBanditLoot']),
        # InteractiveObjectLootListSource('Epic Chest Hyperion', ['GD_Itempools.ListDefs.EpicChestHyperionLoot']),
        # InteractiveObjectLootListSource('Epic Chest Red', ['GD_Itempools.ListDefs.EpicChestRedLoot']),
        # InteractiveObjectLootListSource('Standard Pile', ['GD_Itempools.ListDefs.StandardPileLoot']),
        # InteractiveObjectLootListSource('Storage Locker', ['GD_Itempools.ListDefs.StorageLockerLoot']),
        # InteractiveObjectLootListSource('Weapon Chest Bandit', ['GD_Itempools.ListDefs.WeaponChestBanditLoot']),
        # InteractiveObjectLootListSource('Weapon Chest White', ['GD_Itempools.ListDefs.WeaponChestWhiteLoot']),
        #
        # ItemPoolListSource('Uranus', ['GD_Anemone_ItemPools.ListDefs.Shower_Loot_Boss'] * 6 + [
        #     'GD_Anemone_ItemPools.ListDefs.Boss_Loot_Legendary100']),
        # ItemPoolListSource('Cassius', ['GD_Anemone_ItemPools.ListDefs.Shower_Loot_Boss'] * 5 + [
        #     'GD_Anemone_ItemPools.ListDefs.Boss_Loot_Legendary100']),
        # ItemPoolListSource('Haderax - No Chests', ['GD_Anemone_ItemPools.ListDefs.Shower_Loot_Boss'] * 7 + [
        #     'GD_Anemone_ItemPools.ListDefs.RaidBossEnemyGunsAndGear']),
        # InteractiveObjectLootListSource('Loot Train', ['GD_Allium_Lootables.ListDefs.LootCarLA']),
    ]

    result_dict = {}
    clipboard_string = ''
    for source in sources:
        Log(f"{source.name}: {[format(float(p), '.4%') for p in source.success_dist]}")
        str_list = [source.name] + [format(float(p), '.4%') for p in source.success_dist]
        clipboard_string += '\t'.join(str_list) + '\n'


    subprocess.run(['powershell', '-command', f"Set-Clipboard -Value '{clipboard_string}'"])
