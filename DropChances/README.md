## Drop Chances

This is a utility for finding drop odds from various loot sources.

### Usage

Only drops.py and balances.json are needed. Other files are potentially
useful utilities.

- In the drops.py file, set the _BALANCE_REF_PATH to where you're storing that file. Should be relative to the Win32
  directory in your game folder.
- Set the _SUCCESS_DEF. This can be any function that takes an InventoryBalanceDefinitionWrapper as its arg, and returns
  a bool. Generally you'll want to mess with the rarity and item_type fields to create your result. For example, if you
  wanted any Legandary+ weapon or item, you'd
  set: `_SUCCESS_DEF = lambda inv_bal: inv_bal.rarity.category == 'Legendary+' and inv_bal.item_type.category != 'Other'`
  If you wanted the chance of any blue class mod, it would instead
  be: `_SUCCESS_DEF = lambda inv_bal: inv_bal.rarity == Rarity.Blue and inv_bal.item_type == ItemType.ClassMod`
- Define all the drop sources. There are various ways to define drop sources. These generally require the string path
  name, which can be found in OpenBLCMM.
    - From a set of ItemPoolListDefinitions
    - From sets of ItemPools and ItemPoolListDefinitions
    - From sets of LootConfigurationData
    - From sets of InteractiveObjectLootListDefinition
    - From an InteractiveObjectBalanceDefinition
- Load your character into any map. If you load into NVHM or TVHM, the level of your character will not matter. In UVHM,
  you'll want
  to pay attention to your level, as the drop odds depend heavily on your level in this playthrough.
- In console, run `pyexec drops.py`. The game will freeze for a bit while it's processing. More drop sources will take
  longer, especially sources that have a lot of pools (such as Haderax).
- The result will print to console AND be put on your clipboard in a format that can be pasted into Excel or Google
  Sheets. Results are formatted as chance of getting exactly the number of successes from the source, where the last
  result is the combined chance of 4+ successes.
    - [50.0000%, 30.0000%, 10.0000%, 6.0000%, 4.0000%] means 50% chance of no successes, 30% chance of exactly 1, 10%
      chance of exactly 2, 6% chance of exactly 3, and 4% chance of 4 or more.