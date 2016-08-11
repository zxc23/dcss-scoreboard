"""Defines useful constants."""

import re
from collections import namedtuple

Race = namedtuple('Race', ['short', 'full', 'playable'])
Background = namedtuple('Background', ['short', 'full', 'playable'])
God = namedtuple('God', ['name', 'playable'])

SPECIES = {Race('Ce', 'Centaur', True),
           Race('DD', 'Deep Dwarf', True),
           Race('DE', 'Deep Elf', True),
           Race('Dg', 'Demigod', True),
           Race('Dr', 'Draconian', True),
           Race('Ds', 'Demonspawn', True),
           Race('Fe', 'Felid', True),
           Race('Fo', 'Formicid', True),
           Race('Gh', 'Ghoul', True),
           Race('Gr', 'Gargoyle', True),
           Race('HE', 'High Elf', True),
           Race('HO', 'Hill Orc', True),
           Race('Ha', 'Halfling', True),
           Race('Hu', 'Hunter', True),
           Race('Ko', 'Kobold', True),
           Race('Mf', 'Merfolk', True),
           Race('Mi', 'Minotaur', True),
           Race('Mu', 'Mummy', True),
           Race('Na', 'Naga', True),
           Race('Op', 'Octopode', True),
           Race('Og', 'Ogre', True),
           Race('Sp', 'Spriggan', True),
           Race('Te', 'Tengu', True),
           Race('Tr', 'Troll', True),
           Race('VS', 'Vine Stalker', True),
           Race('Vp', 'Vampire', True),
           # Non-playable races
           Race('El', 'Elf', False),
           Race('Gn', 'Gnome', False),
           Race('OM', 'Ogre-Mage', False),
           Race('HD', 'Hill Dwarf', False),
           Race('MD', 'Mountain Dwarf', False),
           Race('GE', 'Grey Elf', False),
           Race('SE', 'Sludge Elf', False),
           Race('LO', 'Lava Orc', False),
           Race('Dj', 'Djinni', False),
           Race('Pl', 'Plutonian', False),
           Race('??', 'Unknown', False), }

BACKGROUNDS = {Background('AE', 'Air Elementalist', True),
               Background('AK', 'Abyssal Knight', True),
               Background('AM', 'Arcane Marksman', True),
               Background('Ar', 'Artificer', True),
               Background('As', 'Assassin', True),
               Background('Be', 'Berserker', True),
               Background('CK', 'Chaos Knight', True),
               Background('Cj', 'Conjuror', True),
               Background('EE', 'Earth Elementalist', True),
               Background('En', 'Enchanter', True),
               Background('FE', 'Fire Elementalist', True),
               Background('Fi', 'Fighter', True),
               Background('Gl', 'Gladiator', True),
               Background('Hu', 'Hunter', True),
               Background('IE', 'Ice Elementalist', True),
               Background('Mo', 'Monk', True),
               Background('Ne', 'Necromancer', True),
               Background('Sk', 'Skald', True),
               Background('Su', 'Summoner', True),
               Background('Tm', 'Transmuter', True),
               Background('VM', 'Venom Mage', True),
               Background('Wn', 'Wanderer', True),
               Background('Wr', 'Warper', True),
               Background('Wz', 'Wizard', True),
               # Non-playable backgrounds
               Background('Cr', 'Crusader', False),
               Background('DK', 'Death Knight', False),
               Background('He', 'Healer', False),
               Background('He', 'Healer', False),
               Background('Pa', 'Paladin', False),
               Background('Pa', 'Paladin', False),
               Background('Pr', 'Priest', False),
               Background('Re', 'Reaver', False),
               Background('St', 'Stalker', False),
               Background('Th', 'Thief', False),
               Background('Jr', 'Jester', False),
               Background('??', 'Unknown', False), }

GODS = {God('Ashenzari', True),
        God('Atheist', True),
        God('Beogh', True),
        God('Cheibriados', True),
        God('Dithmenos', True),
        God('Elyvilon', True),
        God('Fedhas', True),
        God('Gozag', True),
        God('Hepliaklqana', True),
        God('Jiyva', True),
        God('Kikubaaqudgha', True),
        God('Lugonu', True),
        God('Makhleb', True),
        God('Nemelex Xobeh', True),
        God('Okawaru', True),
        God('Pakellas', True),
        God('Qazlal', True),
        God('Ru', True),
        God('Sif Muna', True),
        God('The Shining One', True),
        God('Trog', True),
        God('Uskayaw', True),
        God('Vehumet', True),
        God('Xom', True),
        God('Yredelemnul', True),
        God('Zin', True),
        # Non-playable gods
        God('Unknown', False), }

PLAYABLE_SPECIES = {s for s in SPECIES if s.playable}
PLAYABLE_BACKGROUNDS = {b for b in BACKGROUNDS if b.playable}
PLAYABLE_GODS = {g for g in GODS if g.playable}
NONPLAYABLE_COMBOS = ['FeGl', 'FeAs', 'FeHu', 'FeAM', 'DgBe', 'DgCK', 'DgAK',
                      'GhTm', 'MuTm']
PLAYABLE_COMBOS = ('%s%s' % (rc.short, bg.short)
                   for rc in PLAYABLE_SPECIES for bg in PLAYABLE_BACKGROUNDS
                   if '%s%s' % (rc, bg) not in NONPLAYABLE_COMBOS)
GOD_NAME_FIXUPS = {
    # Actually, the ingame name is 'the Shining One', but that looks
    # ugly since the capitalisation is wrong.
    'the Shining One': 'The Shining One',
    # Old name
    'Dithmengos': "Dithmenos",
    'Iashol': 'Ru',
    'Ukayaw': 'Uskayaw',
    # Nostalgia names
    'Lugafu': 'Trog',
    'Lucy': 'Lugonu',
}
RACE_SHORTNAME_FIXUPS = { 'Ke': 'Te', 'DS': 'Ds', 'DG': 'Dg' }
RACE_NAME_FIXUPS = {
    'Yellow Draconian': 'Draconian',
    'Grey Draconian': 'Draconian',
    'White Draconian': 'Draconian',
    'Green Draconian': 'Draconian',
    'Purple Draconian': 'Draconian',
    'Mottled Draconian': 'Draconian',
    'Black Draconian': 'Draconian',
    'Red Draconian': 'Draconian',
    'Pale Draconian': 'Draconian',
    'Grotesk': 'Gargoyle',
    'Kenku': 'Tengu',
}
BRANCH_NAME_FIXUPS = {
    # April fool's one year
    'Nor': 'Coc',
    # Rename
    'Vault': 'Vaults'
}
RACE_TO_GREAT_RACE = {'Ce': 'greatcentaur',
                      'DD': 'greatdeepdwarf',
                      'DE': 'greatdeepelf',
                      'Dg': 'greatdemigod',
                      'Ds': 'greatdemonspawn',
                      'Dr': 'greatdraconian',
                      'Fe': 'greatfelid',
                      'Fo': 'greatformicid',
                      'Gh': 'greatghoul',
                      'Gr': 'greatgargoyle',
                      'HE': 'greathighelf',
                      'HO': 'greathillorc',
                      'Ha': 'greathalfling',
                      'Hu': 'greathuman',
                      'Ko': 'greatkobold',
                      'Mf': 'greatmerfolk',
                      'Mi': 'greatminotaur',
                      'Mu': 'greatmummy',
                      'Na': 'greatnaga',
                      'Op': 'greatoctopode',
                      'Og': 'greatogre',
                      'Sp': 'greatspriggan',
                      'Te': 'greattengu',
                      'Tr': 'greattroll',
                      'VS': 'greatvinestalker',
                      'Vp': 'greatvampire', }
ROLE_TO_GREAT_ROLE = {'AE': 'greatairelementalist',
                      'AK': 'greatabyssalknight',
                      'AM': 'greatarcanemarksman',
                      'Ar': 'greatartificer',
                      'As': 'greatassassin',
                      'Be': 'greatberserker',
                      'CK': 'greatchaosknight',
                      'Cj': 'greatconjurer',
                      'DK': 'greatdeathknight',
                      'EE': 'greatearthelementalist',
                      'En': 'greatenchanter',
                      'FE': 'greatfireelementalist',
                      'Fi': 'greatfighter',
                      'Gl': 'greatgladiator',
                      'He': 'greathealer',
                      'Hu': 'greathunter',
                      'IE': 'greaticeelementalist',
                      'Mo': 'greatmonk',
                      'Ne': 'greatnecromancer',
                      'Sk': 'greatskald',
                      'Su': 'greatsummoner',
                      'Tm': 'greattransmuter',
                      'VM': 'greatvenommage',
                      'Wn': 'greatwanderer',
                      'Wr': 'greatwarper',
                      'Wz': 'greatwizard', }

Branch = namedtuple('Branch', ['short', 'full', 'multilevel', 'playable'])
BRANCHES = {
    Branch('D', 'Dungeon', True, True),
    Branch('Lair', 'Lair of the Beasts', True, True),
    Branch('Temple', 'Ecumenical Temple', False, True),
    Branch('Orc', 'Orcish Mines', True, True),
    Branch('Vaults', 'Vaults', True, True),
    Branch('Snake', 'Snake Pit', True, True),
    Branch('Swamp', 'Swamp', True, True),
    Branch('Shoals', 'Shoals', True, True),
    Branch('Spider', 'Spider Nest', True, True),
    Branch('Elf', 'Elven Halls', True, True),
    Branch('Zig', 'Ziggurat', True, True),
    Branch('Depths', 'Depths', True, True),
    Branch('Abyss', 'Abyss', True, True),
    Branch('Sewer', 'Sewer', False, True),
    Branch('Pan', 'Pandemonium', False, True),
    Branch('Crypt', 'Crypt', True, True),
    Branch('Slime', 'Slime Pits', True, True),
    Branch('Zot', 'Realm of Zot', True, True),
    Branch('Ossuary', 'Ossuary', False, True),
    Branch('IceCv', 'Ice Cave', False, True),
    Branch('Hell', 'Vestibule of Hell', False, True),
    Branch('Lab', 'Labyrinth', False, True),
    Branch('Bailey', 'Bailey', False, True),
    Branch('Volcano', 'Volcano', False, True),
    Branch('Tomb', 'Tomb of the Ancients', True, True),
    Branch('Dis', 'Iron City of Dis', True, True),
    Branch('Tar', 'Tartarus', True, True),
    Branch('Geh', 'Gehenna', True, True),
    Branch('Coc', 'Cocytus', True, True),
    Branch('Bazaar', 'Bazaar', False, True),
    Branch('WizLab', "Wizard\'s Laboratory", False, True),
    Branch('Trove', 'Treasure Trove', False, True),
    # Non-playable branches
    Branch('Hive', 'Hive', True, False),
    Branch('Blade', 'Hall of Blades', True, False),
    Branch('Forest', 'Enchanted Forest', True, False),
}
MANUAL_ACHIEVEMENTS = {
    'comborobin': {
        'greatestplayer': True
    },
    'Stabwound': {
        '0.4_winner': True
    },
    '78291': {
        '0.5_winner': True
    },
    'elliptic': {
        '0.7_winner': True,
        '0.10_winner': True
    },
    'mikee': {
        '0.8_winner': True
    },
    'theglow': {
        '0.9_winner': True,
        '0.11_winner': True
    },
    'jeanjacques': {
        '0.12_winner': True
    },
    'bmfx': {
        '0.13_winner': True
    },
    'Tolias': {
        '0.14_winner': True,
        '0.15_winner': True
    },
    'DrKe': {
        '0.16_winner': True
    },
    'cosmonaut': {
        '0.17_winner': True
    },
}
GLOBAL_TABLE_LENGTH = 10
PLAYER_TABLE_LENGTH = 10
BLACKLISTS = {'griefers': {},
              'bots':
              {'autorobin', 'xw', 'auto7hm', 'rw', 'qw', 'ow', 'qwrobin', 'gw',
               'notqw', 'jw', 'parabodrick', 'hyperqwbe', 'cashybrid',
               'tstbtto', 'parabolic', 'oppbolic', 'ew', 'rushxxi', 'gaubot',
               'cojitobot', 'paulcdejean', 'otabotab', 'nakatomy', 'testingqw',
               'beemell', 'beem', 'drasked', 'phybot'}}
TABLE_CLASSES = "table table-hover table-striped"
LOGFILE_REGEX = re.compile('(logfile|allgames)')
MILESTONE_REGEX = re.compile('milestone')
KTYPS = ("mon",
         "beam",
         "quitting",
         "leaving",
         "pois",
         "winning",
         "acid",
         "cloud",
         "disintegration",
         "wild_magic",
         "starvation",
         "trap",
         "spore",
         "burning",
         "targeting",
         "draining",
         "water",
         "rotting",
         "something",
         "curare",
         "stupidity",
         "bounce",
         "targetting",
         "self_aimed",
         "spines",
         "rolling",
         "lava",
         "barbs",
         "falling_down_stairs",
         "divine_wrath",
         "xom",
         "weakness",
         "clumsiness",
         "being_thrown",
         "wizmode",
         "beogh_smiting",
         "headbutt",
         "mirror_damage",
         "freezing",
         "reflect",
         "collision",
         "petrification",
         "tso_smiting",
         "falling_through_gate", )
KTYP_FIXUPS = {
    # Renames
    'divine wrath': 'divine_wrath',
    'wild magic': 'wild_magic',
}
