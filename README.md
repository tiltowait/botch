<p align="center">
	<a href="https://discord.gg/QHnCdSPeEE" title="Join the official server"><img src="https://img.shields.io/discord/935219170176532580?color=5765F2&label=discord&logo=discord&logoColor=white" alt="Discord member count" /></a>
	<a href="https://www.patreon.com/tiltowait" title="Support me on Patreon!"><img src="https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.vercel.app%2Fapi%3Fusername%3Dtiltowait%26type%3Dpatrons&style=flat" alt="Patreon" /></a>
	<br>
	<a href="https://github.com/tiltowait/botch/blob/master/LICENSE" title="License"><img src="https://img.shields.io/github/license/tiltowait/botch" alt="MIT license" /></a>
	<img src="https://img.shields.io/github/actions/workflow/status/tiltowait/botch/ci.yml" alt="Build status">
	<a href="https://app.codecov.io/gh/tiltowait/botch", title="Code coverage report"><img src="https://img.shields.io/codecov/c/github/tiltowait/botch" alt="Code coverage"></a>
</p>

# 🤖 Botch

**Botch** is a Discord bot for *World of Darkness* and *Chronicles of Darkness*. It features a dice roller incorporating character traits (so you can type e.g. `Strength + Brawl` instead of a non-descriptive number), plus character stats tracking and, for [premium supporters](https://patreon.com/tiltowait), image uploads.

## 🎲 Key features

* Character sheet management via Discord application commands
* Dice rolling with character sheet integration
* Custom macros for common rolls
* Willpower integration in rolls
* Specialties and Custom Traits
* Support for multiple WoD/CofD game systems
* Premium features, including image uploads
* Easy-to-use commands with natural syntax
* Web-based character creation wizard
* Comprehensive help menu

A comprehensive reference is available in [the documentation](https://docs.botch.lol).

## ⌨️ Example commands

```
/roll pool:dexterity+brawl difficulty:6
/mroll macro:hunt
/traits assign traits:Spelunking=3; Hot Air Ballooning=2
```

## 🕹️ Supported games

The bot is designed from the ground-up to be modular and extensible, allowing it to support multiple game lines. Currently supported games are:

### 🌒 World of Darkness

* *Vampire: The Masquerade*
	* Both Final Nights and Dark Ages variants
	* Mortals, Ghouls, Vampires

### 🌑 Chronicles of Darkness

* *Vampire: The Requiem*
	* Mortals and Vampires
* *Mummy: The Curse*
	* Mummies

Due to the differences between the Storyteller and Storytelling systems, **Botch** is available in two flavors:

* **Botch**, for *World of Darkness* (20th Anniversary Edition)
* **Beat**, for *Chronicles of Darkness* (2E)

### 🔎 Looking for V5?

Check out [Inconnu](https://github.com/tiltowait/inconnu)! It has many (and more!) of the same features.

## 🚀 Getting started

If you simply want to install either bot on your Discord server, you'll find installation links in [the official documentation](https://docs.botch.lol).

If you want to run the bot(s) locally, either for personal use or to contribute, read on.

### ✅ Requirements

* [Poetry](https://python-poetry.org/)
* A registered [Discord application](https://discord.com/developers/docs/intro)
* A MongoDB database
* Emojis (default set found in the `assets` directory) installed in the server on which the bot will run. (At present, the [Pycord](https://pycord.dev/) library on which the bot is based does not support application emojis.)

### ⚙️ Environment variables

This repo contains three environment template files:

* `.env.template`
* `.env.botch.template`
* `.env.beat.template`

Each contains documentation on the expected parameters. If you wish to do local testing, it's highly recommended to set the `DEBUG` variable.

### 🏃‍♂️ Running

1. Install dependencies: `poetry install`
1. Copy `.env` templates and supply variables:
	- `.env.template` → `.env`
	- `.env.botch.template` → `.env.botch`
	- `.env.beat.template` → `.env.beat`
1. Run the bot: `poetry run botch` or `poetry run beat`

## 🔮 Future plans

* Web app
* Convenience commands (such as a single command for Vampires to spend blood and heal)
* More character templates

### ❓ Will it support *X* game line?

If *X* is a WoD20 or CofD 2E game, then: Maybe! It will depend on both personal and community interest.

