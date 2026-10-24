-- Chris --

(These files originate from http://www.stacken.kth.se/~skrolle/gouki/)

Topics:

* What's this?
* What's needed?
* What's new?
* Comments
* What's done?
* What's left?
* Moveslist
* Credits

-- What's this? --

This is Chris from The king of fighters '97 and '98, adapted for play with
Elecbyte's fighting game engine M.U.G.E.N. by me, NeoGouki (gouki@hem.passagen.se).

-- What's needed? --

First of all, the newest revision of the M.U.G.E.N. engine which can be found
at http://www.elecbyte.com. Secondly, all the files contained within
the archive chris.zip which are:

* chris.def
* chris.sff
* chris.snd
* chris.cns
* chris.cmd
* kof97a.act
* kof97b.act
* kof97c.act
* kof97d.act
* kof97e.act
* kof97f.act
* kof97g.act
* kof97h.act
* kof98a.act
* kof98b.act
* kof98c.act
* kof98d.act
* kof98e.act
* kof98f.act
* kof98g.act
* kof98h.act

Unzip all the files into a sub-directory to the directory where you keep the
M.U.G.E.N. engine called "chars\chris" and add the character to your
character roster by simply adding the line "chris" to your "select.cfg"
under the [Characters] section.

-- What's new? --

* Changed the timing for the light kick/light punch combos to be more accurate.
* Added guard cancel roll back/forward and guard cancel knockdown attack.
* Changed some things about the Direction change that would make the commands reverse.
* Changed to a more stylish timer for the O. mode. :)
* Added some CLSN2 to the POW MAX animation.

-- Comments --

Once again, there are more palettes than MUGEN can handle at one time, so you're
free to choose the ones you like the best. Chris has also gotten the "Mary treatment",
which means that you can at any time pull off desperation moves with a weak attack
(takes 1 level of power) and super desperation moves with a hard attack
(takes 2 levels of power). However, if you're low on life (150 or below) you can do DMs
at will and once your power bar reaches level 1 any DM automatically becomes a SDM.
Chris can also transform into his Orochi incarnation by executing the
"Orochi no chikara o mezameru" command. It costs 2000 in power and lasts for
a limited amount of time.

-- What's done? --

* 3 pre-fight intros
* 6 win poses
* 4 taunts
* 2 Time over loss animation
* All getting hit, guarding and falling animations
* All required frames
* Running forward, dashing back
* All standing, crouching and jumping normal attacks
* Strike attack
* Attack evade and attack evade follow-up
* Emergency evade back and forward
* Power build
* Two throws
* Scramble dash
* Hunting air
* Glider stamp
* Slide touch
* Shooting dancer thrust
* Shooting dancer step
* Direction change
* Orochi no chikara o mezameru
* Taiyou o iru honoo
* Kagami o hofuru honoo
* Tsuki o tsumu honoo
* Shishi o kamu honoo
* Twister drive
* Chain slide touch
* Ankoku orochi nagi
* Daichi o harau gouka
* Orochi no chikara o mezameru

-- What's left? --

Nothing...?

-- Moveslist --

> Both modes <

  Low jump
        - Tap U
  Long jump
        - D, U (for long short jumps, D, tap U)
  Light punch
        - X
  Light kick
        - A
  Hard punch
        - Y
  Hard kick
        - B
  Taunt
        - Start
  Spinning array/Muyou no ono
        - F + X
  Reverse anchor kick/Jukei no oni
        - F + A
  Carry off kick/Setsudan no koto
        - DF + A
        - Crouching
  Step turn/Chi no batsu (throw A)
        - F + Y
        - Close to the opponent
  Aerial drop/Ten no tsumi (throw B)
        - F + B
        - Close to the opponent
  Strike attack
        - C / Y + B
        - Can also be done in the air
        - Can also be used as a guard cancel, if power is at 500 or above
  Attack evade
        - Z / X + A
  Attack evade follow-up attack
        - Any normal attack during attack evade
  Emergency roll
        - F or B + Z / X + A
        - Can also be used as a guard cancel, if power is at 500 or above
  Power build
        - Press and hold X + A + Y

> Normal mode <

  Scramble dash
        - D, DF, F + A or B
  Hunting air
        - F, D, DF + A or B
  Glider stamp
        - D, DF, F + A or B
        - In the air
  Slide touch
        - D, DF, F + X or Y
  Shooting dancer thrust
        - F, DF, D, DB, B + X or Y
  Shooting dancer step
        - F, DF, D, DB, B + A or B
  Direction change
        - F, D, DF + X or Y
  Twister drive (DM)
        - D, DB, B, D, DB, B + A
        - Power level is at 1000 or higher
        - Or life below 150
  Twister drive (SDM)
        - D, DB, B, D, DB, B + B
        - Power level is at 2000 or higher
        - Or life is below 150 and power level is at 1000 or higher
  Chain slide touch (DM)
        - D, DF, F, D, DF, F + X
        - Power level is at 1000 or higher
        - Or life is below 150
  Chain slide touch (SDM)
        - D, DF, F, D, DF, F + Y
        - Power level is at 2000 or higher
        - Or life is below 150 and power level is at 1000 or higher
  Orochi no chikara o mezameru
        - D, DB, B, D, DB, B + X or Y
        - Power level is at 2000 or higher 

> Orochi mode <

  Taiyou o iru honoo
        - D, DF, F + X or Y
  Kagami o hofuru honoo
        - D, DB, B + X or Y
  Tsuki o tsumu honoo
        - F, D, DF + X or Y
  Shishi o kamu honoo
        - B, DB, D, DF, F + A or B
        - Close to the opponent
  Ankoku orochi nagi (DM)
        - D, DB, B, DB, D, DF, F + X
        - Power level is at 1000 or higher
        - Or life below 150
  Ankoku orochi nagi (SDM)
        - D, DB, B, DB, D, DF, F + Y
        - Power level is at 2000 or higher
        - Or life is below 150 and power level is at 1000 or higher
  Daichi o harau gouka (DM)
        - D, DF, F, D, DF, F + X
        - Power level is at 1000 or higher
        - Or life is below 150
  Daichi o harau gouka (SDM)
        - D, DF, F, D, DF, F + Y
        - Power level is at 2000 or higher
        - Or life is below 150 and power level is at 1000 or higher

-- Credits --

* SNK, for making the much credited King of fighters series so that I had something to steal from.
* I have to credit myself of course, for taking the time to convert
  this character to the M.U.G.E.N. format.
* Elecbyte, for creating the wonderful M.U.G.E.N. engine and letting us experience
  the match-ups of our dreams.
* TESTP, for being a great support in the everyday struggle of character making
  and being nice guys in general.
* ShadoWatc, for helping me poke around in my CNS to make sure it's playable.
* All the great guys and girls over at the TESTP message board who can be a
  great resource from time to time.