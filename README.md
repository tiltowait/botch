<p align="center">
	<img src="https://img.shields.io/github/license/tiltowait/botch" alt="MIT license" />
	<img src="https://img.shields.io/circleci/build/github/tiltowait/botch/master" alt="Build status">
	<img src="https://img.shields.io/codecov/c/github/tiltowait/botch" alt="Code coverage">
</p>

# Botch

Botch is a very (very!) slow WIP that will eventually, hopefully, become a multi-system Discord dice bot and character manager for World of Darkness and Chronicles of Darkness games.

In the meantime, check out [[Tzimisce]](https://tzimisce.app) for a basic X20 Wod/CofD dice bot. Check out [Inconnu](https://inconnu.app) for a fully-featured V5 dice bot and character manager.

## Background

I'd call this the FAQ section, only that feels disingenouus when no one's asked me anything. So, to head off those potential questions ...

### Why not add this functionality to [Tzimisce]?

[Tzimisce] is my first-ever bot, and my first "real" Python project. While I have a lot of nostalgia for it, it is ... something of a mess, to put it mildly. Adding complex features is a challenge, modules are constructed strangely, and the effort to improve it to the point that it would work with Botch's planned feature set would be more work than simply starting over.

There's also something to be said for familiarity. A new bot allows me to create new interaction conventions that don't mesh well with [Tzimisce]'s design. Inevitably, there will be people who just want to stick with what they know, and it wouldn't be fair to them to take away something that, from their perspective, works just fine.

### Okay. So why not add to Inconnu?

Inconnu's a far more advanced bot than [Tzimisce], and it has many of the features Botch will have. However, Inconnu isn't designed to handle multiple game lines. Like [Tzimisce], it would need substantial refactoring to get it to that point. There's also the fact that X20 and CofD have very different dice mechanics compared to V5. It just doesn't make sense to try to tack on two vastly different systems to a bot that's already in a healthy spot.

### What's in a name?

Why Botch? Botches are bad! Yes, they are. Over the years, many users have contacted me to complain that they're getting too many botches. In reality, it's just confirmation bias at work: you remember the bad rolls more strongly than you remember the good rolls. It's human nature. In actuality, a good PRNG (programmable random number generator) is more random than any set of dice you'll buy at your FLGS.
