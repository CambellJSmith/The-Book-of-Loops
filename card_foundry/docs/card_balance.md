# encounter balance

The 399 ordinary monsters form three equal groups. Species identity, element, artwork prompt and move names remain individual; combat statistics are identical within each group so a faster or higher-damage species does not quietly dominate its peers.

| species ids | difficulty | count | health | speed | move 1 damage | move 2 damage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0001–0133 | easy | 133 | 120 | 30 | 20 | 40 |
| 0134–0266 | medium | 133 | 240 | 60 | 40 | 80 |
| 0267–0399 | hard | 133 | 480 | 90 | 80 | 160 |
| 0400 | boss | 1 | 2400 | 120 | 160 | 320 |

Move 1 costs 1 mana and move 2 costs 2 mana for every card. Every ordinary tier doubles health and damage; speed rises enough that the next tier acts first. These are encounter groups, not evolution stages. Types remain evenly distributed across the whole set: 80 of each, with the dark boss included in the dark total. Within a tier each type appears 26 or 27 times because 133 does not divide evenly by five.

## chronourobor — species 0400

Chronourobor is a dark-type time sovereign: a monumental armored serpent whose body makes an upright ouroboros loop around an hourglass heart. Upward-flowing silver sand, concentric clockwork rings, clock-hand horns and closed ribbons of frozen moments express its control over repeating time. Its full watercolor prompt is saved on the card; artwork remains empty.

- **secondhand sever** — 1 mana, 160 damage: the creature cuts across an opponent's immediate future.
- **closed eternity** — 2 mana, 320 damage: it confines the target to a repeating instant of impact.

The time descriptions are flavor and visual direction. The current card format contains direct damage, not executable rewind, extra-turn, healing or time-lock effects. No such hidden powers are included in the numerical balance.

## reference encounter model

The reproducible check in `scripts/verify_card_balance.py` assumes all monsters begin at full health, each living monster acts once per round in descending speed order, each receives enough mana to use move 2 each round, all damage is single-target, and there are no items, type bonuses, healing, critical hits or additional effects. The boss focuses one target until it is defeated. Defeated monsters do not act. Each player monster attacks the boss.

Under that model:

- Identical same-tier monsters are interchangeable; the first actor wins a duel, so initiative ties must be resolved fairly by the final game rules.
- Every medium defeats every easy, and every hard defeats every medium.
- Chronourobor defeats teams of one, two or three hard monsters.
- Four hard monsters defeat it in six rounds, with one survivor. Larger teams have more margin.

This is an explicit four-hard-monster encounter target, not a guarantee under undefined combat rules. Changing mana regeneration, attack frequency, targeting, elemental bonuses or adding time powers requires retuning the boss and rerunning encounter checks. This editor does not implement a battle engine.

## saved collection update

The application applies this balance once to the original set's stable record identities, increments revisions to reject stale saves, and records completion atomically. It preserves uploaded artwork, framing, ordinary monster names, ordinary move names and ordinary prompts. Only species 0400 receives the new boss name, prompt and move names. Deleted cards are not recreated; cards added by the user are not modified. Later manual edits are preserved on reopening.
