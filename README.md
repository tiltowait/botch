<p align="center">
	<a href="https://discord.gg/QHnCdSPeEE" title="Join the Inconnu server"><img src="https://img.shields.io/discord/935219170176532580?color=5765F2&label=discord&logo=discord&logoColor=white" alt="Discord member count" /></a>
	<a href="https://www.patreon.com/tiltowait" title="Support me on Patreon!"><img src="https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.vercel.app%2Fapi%3Fusername%3Dtiltowait%26type%3Dpatrons&style=flat" alt="Patreon" /></a>
	<br>
	<a href="https://github.com/tiltowait/botch/blob/master/LICENSE" title="License"><img src="https://img.shields.io/github/license/tiltowait/botch" alt="MIT license" /></a>
	<img src="https://img.shields.io/github/actions/workflow/status/tiltowait/botch/ci.yml" alt="Build status">
	<a href="https://app.codecov.io/gh/tiltowait/botch", title="Code coverage report"><img src="https://img.shields.io/codecov/c/github/tiltowait/botch" alt="Code coverage"></a>
</p>

# Botch

Botch is a pair of Discord bots (called Botch and Beat) for playing *Vampire: The Masquerade* and *Vampire: The Requiem* games over Discord. They feature a dice roller incorporating character traits (so you can type `Strength + Brawl` instead of a non-descriptive number, *a la* my other bot, [Inconnu](https://github.com/tiltowait/inconnu)), plus character stats tracking and, for premium supporters, image uploads.

Botch is being designed from the ground up to be modular and extensible, meaning it can eventually expand to other World/Chronicles of Darkness game lines, depending on community and personal interest.

## Current status

Botch is currently in beta on the [official server](https://discord.gg/QHnCdSPeEE). After a short testing period, it will open to all users on The Second City (link above). For general release, [check the milestone](https://github.com/tiltowait/botch/milestone/2) to see current progress.

**Need a bot now?** Check out [[Tzimisce]](https://tzimisce.app) for a basic X20 Wod/CofD dice bot without character tracking features. Or add [Inconnu](https://inconnu.app) for a fully-featured V5 dice bot and character manager.

## Background

I'd call this the FAQ section, only that feels disingenuous when no one's asked me anything. So, to head off those potential questions ...

### Why not add this functionality to [Tzimisce]?

[Tzimisce] is my first-ever bot, and my first "real" Python project. While I have a lot of nostalgia for it, it is ... something of a mess, to put it mildly. Adding complex features is a challenge, modules are constructed strangely, and the effort to improve it to the point that it would work with Botch's planned feature set would be more work than simply starting over.

There's also something to be said for familiarity. A new bot allows me to create new interaction conventions that don't mesh well with [Tzimisce]'s design. [Tzimisce] has thousands of users. Inevitably, there will be people who just want to stick with what they know, and it wouldn't be fair to them to take away something that, from their perspective, already works just fine.

### Okay, so why not add to Inconnu?

Inconnu's a far more advanced bot than [Tzimisce], and it has many of the features Botch will have. However, Inconnu isn't designed to handle multiple game lines. Like [Tzimisce], it would need substantial refactoring to get it to that point. There's also the fact that X20 and CofD have very different dice mechanics compared to V5. It just doesn't make sense to try to tack on two vastly different systems to a bot that's already in a healthy spot.

### What's in a name?

Why Botch? Botches are bad! Yes, they are. Over the years, many users have contacted me to complain that botch too often. In reality, it's just confirmation bias at work: you remember the bad rolls more strongly than you remember the good rolls. It's human nature. In actuality, a good PRNG (programmable random number generator), like these bots use, is more random than any set of dice you'll buy at your FLGS.

### Will it support `X`?

If your hypothetical game is a WoD20 or CofD 2E game, then: Maybe!
