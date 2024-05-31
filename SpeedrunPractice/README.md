# Speedrun Practice Mod

Borderlands 2 mod with various utilities to help in practicing speedruns. Currently supported are Gaige (Any% and All
Quests) and Geared Sal.

## Installation

1. Make sure the BL2 Python SDK is installed according to https://bl-sdk.github.io/
2. This mod has the following dependencies:
    1. Borderlands Commander v2.5: https://bl-sdk.github.io/mods/BorderlandsCommander/
3. Extract the SpeedrunPractice.zip file in this repo and copy the SpeedrunPractice folder to binaries/Win32/Mods in
   the game folder
4. If you plan to use the checkpoint saver, edit the "config.json" file to reflect your local save directory.
5. Launch the game, select "Mods" from the main menu, then enable SpeedrunPractice

## Features

### Block achievements

Accidental presses of the Achievements menu option no longer open Steam/Epic

### Disable travel portal

There's an option in the menu to disable the blue tunnel on entering a level at a fast travel station. Helpful for 
faster practice when level reloads are needed.

### Move save to top

Keybind to use `touch` command to set the modified time of your save file to current time, which effectively brings it
to the top of the list when choosing saves in the character menu.

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

For non-Gaige characters, only relevant values are saved. For example, Salvador geared will only save the map position,
while Axton Any% will save all but Buck Up, Anarchy, and Smasher stacks.

### Patch 1.1 simulation

- Amp damage - Multiplies amp shield bonus by the number of pellets on the card when applying the bonus to the weapon.
  In effect this mimics the behavior of old game versions that applied full amp damage to every pellet. Only applies
  when patch 1.1 is set in options menu.
- Weapon merging - Mimics the old weapon merging glitch that keeps various weapon bonuses the player starts swap, enters
  inventory, and swaps the weapon out that they were holding. The game never removes the bonuses from the original gun
  when this happens.
- Vladof free shot glitch - Allows stacking of infinite ammo using a Vladof launcher like in old versions of the game.
- Evil Smasher glitch - Allows stacking of Evil Smasher skills like in old versions of the game.
- DLC expansions removed from Fast Travel - Only base game destination appear in Fast Travel, similar to patch 1.1. I
  was unable to figure out how to remove the  "Borderlands 2" header. This only matters when leaving no U-turn maps. In
  patch 1.1,Sanctuary is already selected, but on current patch with this mod, you'll have to hit down arrow once to get
  back to Sanctuary.
- Three Horns Divide Fast Travel - Just like in patch 1.1, this station becomes available without having to go near it
  to trigger. Becomes available the first time Sanctuary is entered.
- Pickup radius - Pickup radius set to 200 to be in line with older patch behavior.

### Patch 1.3.1 simulation

Same as patch 1.1 except

- Remove amp damage adjustment
- Remove Three Horns Divide Fast Travel glitch

### Stacks and skills keybinds (Any% and All Quests)

Using an in game keybind and input window, can set the following to desired values:

- Anarchy stacks (Gaige only)
- Buck up stacks (Gaige only)
- Free shot stacks (from Vladof launcher)
- Evil Smasher chance stacks (All Quests only)
- Evil Smasher SMASH stacks (All Quests only)
- Merge all equipped weapons

### Show current stacks/bonuses (Any% and All Quests)

A keybind can be set up to show useful game states:

- Number of Buck Up stacks
- Number of free shot stacks
- Number of Evil Smasher chance stacks (All Quests only)
- Number of Evil Smasher SMASH stacks (All Quests only)
- Current critical hit bonus

### Jakobs shotgun auto-fire (Any% and All Quests)

Menu option that makes all Jakobs shotguns auto fire. This is intended to mimic the functionality of the in-game
free scroll macro created by Apple. SDK mods and that macro cannot be installed simultaneously, so I added this option
for practice. Just turn this option on and rebind fire to whatever key you plan to use for the free scroll macro.

### Randomize gear (Any% Gaige only)

A keybind can be set that randomizes your shotgun and shield based on your current story
progress and the vendors you would have checked at that point. When the keybind is pressed, all jakobs shotguns and amp
and turtle shields are dropped in front of you, and new gear from the vendor item pools are equipped or put into your
inventory.

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

### Reset gunzerk (Geared Sal)

Keybind to end gunzerk and reset cooldown. Also fills your rocket ammo and drop swaps all weapons to get them back to
the optimal drop order needed for drop reloading. This works only if you have your damage weapons in slots 1 and 2, with
Badabooms in slots 3 and 4.

### Reset gunzerk, teleport, and trigger skills (Geared Sal)

A separate keybind to do the same thing as reset gunzerk, plus teleport you to the currently active Commander position
with 0 velocity, and trigger skills of your choosing. The skills triggered by this keybind are configurable in the
options menu:

- Incite
- Locked and Loaded
- All kill skills

## Changelog

### Version 1.6

- Added option to disable travel portal (blue tunnel) for faster practice.
- When resetting to commander position as Geared Sal, velocity is now set to 0.

### Version 1.5

- Added Geared Sal functionality.
- Options and keybinds update automatically based on loaded character and speedrun category selection.
- Block achievements from tabbing out your game.
- Add "touch" functionality to move current save to top of list.

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

