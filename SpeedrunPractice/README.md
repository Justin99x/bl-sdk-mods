# Speedrun Practice Mod

BL2 mod that enables various glitches and tricks to help practice Gaige speedruns including Any% and All Quests. 
Gaige in particular is hard to practice late game due to the route including a large build up of anarchy stacks and buck 
up stacks. In addition, the speedruns are done on patches 1.1 and 1.3.1, which does not support Python SDK mods, making 
it impossible to use useful practice tools such as Apple's Borderlands Cheats and Mopioid's Commander, which allow for 
things like infinite ammo and moving around the map instantly.

## Installation

1. Make sure the BL2 Python SDK is installed according to https://bl-sdk.github.io/
2. This mod has the following dependencies:
    1. User Feedback: https://github.com/apple1417/bl-sdk-mods/tree/master/UserFeedback
3. Extract the SpeedrunPractice.zip file in this repo and copy the AnyPercentHelper folder to binaries/Win32/Mods in
   the game folder
4. If you plan to use the checkpoint saver, edit the "config.json" file to reflect your local save directory.
5. Launch the game, select "Mods" from the main menu, then enable Any% Helper

## Features

### Set stacks of skills and anarchy

Using an in game keybind and input window, can set the following to desired values:
- Anarchy stacks
- Buck up stacks
- Free shot stacks (from Vladof launcher)
- Evil Smasher chance stacks
- Evil Smasher SMASH stacks

### Amp damage glitch

Multiplies amp shield bonus by the number of pellets on the card when applying the bonus to the weapon.
In effect this mimics the behavior of old game versions that applied full amp damage to every pellet. Patch 1.3.1 does 
not have this, but it shouldn't be an issue because All Quests routing does not use amp shields.

### Weapon merging

Mimics the old weapon merging glitch that keeps various weapon bonuses the player starts swap, enters inventory, and
swaps the weapon out that they were holding. The game never removes the bonuses from the original gun when this happens.

In addition, can set a keybind to automatically merge bonuses from all weapons in the backpack. Useful for practicing
late game segments without having to manually merge weapons each time.

### Vladof free shot glitch

Allows stacking of infinite ammo using a Vladof launcher like in old versions of the game. An infinite ammo stack can be
added by firing until the free shot is next and either

1) swap away and back to the launcher quickly (and waiting for the ammo graphic to reappear), or
2) drop and pickup the launcher

### Jakobs shotgun auto-fire

Menu option that makes all Jakobs shotguns auto fire. This is intended to mimic the functionality of the in-game
free scroll macro created by Apple. SDK mods and that macro cannot be installed simultaneously, so I added this option
for practice. Just turn this option on and rebind fire to whatever key you plan to use for the free scroll macro.

### DLC expansions removed from Fast Travel

Only base game destination appear in Fast Travel, similar to patch 1.1. I was unable to figure out how to remove the
"Borderlands 2" header. This only matters when leaving no U-turn maps. In patch 1.1,
Sanctuary is already selected, but on current patch with this mod, you'll have to hit down arrow once to get back to
Sanctuary.

### Three Horns Divide Fast Travel

Just like in patch 1.1, this station becomes available without having to go near it to trigger. Becomes available the
first time Sanctuary is entered.

### Pickup radius

Pickup radius set to 200 to be in line with older patch behavior.

### Show current stacks/bonuses

A keybind can be set up to show useful game states:

- Number of Buck Up stacks
- Number of free shot stacks
- Number of Evil Smasher chance stacks
- Number of Evil Smasher SMASH stacks
- Current critical hit bonus
  For the free shot stacks, note that if your target is 2 for a Coach gun, you'll want to have 3 stacks while still
  holding the launcher, as one stack gets removed when you swap away (unless you drop the weapon instead of swap)

### Save checkpoints and game state

A keybind can be set up to save checkpoints to allow for easy replay of the same segments. When the keybind is pressed,
the following actions occur:

- The user is asked for the name of the new file.
- A new save file is created with the current state of the game and set to read only.
- Non-savable game states of Anarchy, Buck Up, Free Shots, Smasher stacks, active weapon, current ammo in clips, 
  Crit Merges, and map position are stored in the actual save file using some unused player stat values. Whenever using
  this save in the future, a second key bind can be used to load those game states, allowing for continuation
  of game play with the same number of stacks and merges applied. Useful for practicing the same late game segments.

It's best to leave the checkpoint files as read only. The player stats are not rewritten when saving regularly, only 
when using the checkpoint feature.

### Randomize gear

A keybind can be set that randomizes your shotgun and shield based on your current story progress and the 
vendors you would have checked at that point. When the keybind is pressed, all jakobs shotguns and amp and turtle
shields are dropped in front of you, and new gear from the vendor item pools are equipped or put into your inventory.

The purpose of this is to be able to practice sections of the game with a wide variety of RNG based gear that you would
likely encounter during normal runs.

Specifically, each of the following items are rolled:
- Frostburn - always get a white Turtle shield
- Sanctuary level 8-10 - always get a Jakobs shotgun with a Jakobs, Bandit, or Torgue barrel
- Fridge level 13-14 - always get an amp shield with at least 100 damage
- Overlook level 14-16 - always get a Jakobs shotgun with a Jakobs, Bandit, or Torgue barrel
- Hyperion Bridge - one attempt to get an amp shield with at least 25 more damage than existing amp
- Wildlife - one attempt to get an amp shield with at least 25 more damage than existing amp
- Thousand Cuts - one attempt to get an amp shield with at least 25 more damage than existing amp

If at any point an amp shield with damage >= 175 is obtained, no more shield vendors are checked.

## Changelog

### Version 1.4.1
- Fixed issue where travel and Jakobs auto fire were not resetting back to normal state when disabling the mod.

### Version 1.4
- Save states are now stored in the save file itself. 
- Added Evil Smasher stacking so that the mod can be used for All Quests.
- Changed keybinds for adding/removing stacks to a single "set" keybind for each.
- Changed internal logic of infinite ammo stacking to exactly mimic the old patches.
- Changed internal logic of weapon merging to exactly mimic the old patches.
- Removed dependency on Commander.

### Version 1.3
- Added gear randomizer keybind.

### Version 1.2

- Fixed issue where save names with letters broke the system - now correctly treats save file numbers as hexadecimal.
- Changed save behavior to keep the current save active and keep the save filename constant, only the newly created save
  increments.
- Pickup radius changed to 200 to mimic version 1.1 functionality.

### Version 1.1

- Removed DLC expansions from the FT menu
- Auto enable Three Horns Divide FT without going to station
- Added keybind to show current stats - buckup, free shots, and crit bonus
- Ability to save checkpoints complete with game state (anarchy, buck up, merged weapons, and map position)
- Games loaded from checkpoint files will load with same weapon as previously active
- Option to make Jakobs shotguns auto-fire

