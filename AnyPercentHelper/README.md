# AnyPercentHelper

BL2 mod that enables various glitches and tricks to help practice Any% Gaige speedruns. Gaige in particular is hard to 
practice late game due to the route including a large build up of anarchy stacks and buck up stacks. In addition, the
speedrun is done on patch 1.1, which does not support Python SDK mods, making it impossible to use useful practice tools 
such as Apple's Borderlands Cheats and Mopioid's Commander, which allow for things like infinite ammo and moving around 
the map instantly.

## Installation
1. Make sure the BL2 Python SDK is installed according to https://bl-sdk.github.io/
2. This mod requires Commander to be installed: https://github.com/mopioid/Borderlands-Commander
3. Extract the AnyPercentHelper.zip file in this repo and copy the AnyPercentHelper folder to binaries/Win32/Mods in
    the game folder
4. If you plan to use the checkpoint saver, edit the "config.json" file to reflect your local save directory.
5. Launch the game, select "Mods" from the main menu, then enable Any% Helper

## Features

### Add or remove Buck Up stacks
Using in game keybinds, add or remove a "stack" of Buck Up.

### Add anarchy stacks
Adds 10 anarchy stacks, up to the maximum stack cap.

### Amp damage glitch
Multiplies amp shield bonus by the number of pellets on the card when applying the bonus to the weapon. 
In effect this mimics the behavior of old game versions that applied full amp damage to every pellet. 

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

In addition, can set a keybind to automatically add or remove a stack of infinite ammo. Useful for practicing
late game segments without having to manually use the launcher to add stacks.

### Jakobs shotgun auto-fire
Menu option that makes all Jakobs shotguns auto fire. This is intended to mimic the functionality of the in-game
free scroll macro created by Apple. SDK mods and that macro cannot be installed simultaneously, so I added this option
for practice. Just turn this option on and rebind fire to whatever key you plan to use for the free scroll macro.

### DLC expansions removed from Fast Travel
Only base game destination appear in Fast Travel, similar to patch 1.1. I was unable to figure out how to remove the 
"Borderlands 2" header. This only matters when leaving Bloodshot Ramparts the End of the Line maps. In patch 1.1, 
Sanctuary is already selected, but on current patch with this mod, you'll have to hit down arrow once to get back to 
Sanctuary.

### Three Horns Divide Fast Travel
Just like in patch 1.1, this station becomes available without having to go near it to trigger. Becomes available the
first time Sanctuary is entered.

### Show current stacks/bonuses
A keybind can be set up to show 3 items:
- Number of Buck Up stacks
- Number of free shot stacks
- Current critical hit bonus
For the free shot stacks, note that if your target is 2 for a Coach gun, you'll want to have 3 stacks while still holding
the launcher, as one stack gets removed when you swap away.

### Save checkpoints and game state
A keybind can be set up to save checkpoints to allow for easy replay of the same segments. When the keybind is pressed, 
the following actions occur:
- The user is asked for the name of the new file.
- The current save file is renamed in the local file system and set to read only.
- A new save file is created with the current state of the game, also read only.
- Non-savable game states of Anarchy, Buck Up, Free Shots, Crit Merges, and map position are stored locally in state.json
Whenever using this save in the future, a second key bind can be used to load those game states, allowing for continuation
of game play with the same number of stacks and merges applied. Useful for practicing the same late game segments.

The game states are loaded according to the hash of the save file. It will not work if the save file is changed in any 
way (e.g. by disabling read only)

## Changelog

### Version 1.1
- Removed DLC expansions from the FT menu
- Auto enable Three Horns Divide FT without going to station
- Added keybind to show current stats - buckup, free shots, and crit bonus
- Ability to save checkpoints complete with game state (anarchy, buck up, merged weapons, and map position)
- Games loaded from checkpoint files will load with same weapon as previously active
- Option to make Jakobs shotguns auto-fire

