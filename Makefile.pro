# PRO scale build.  Every fighter uses the full 1.0 art except Chang (0.80),
# Sakura (0.95) and Billy (0.85).  Writes its own artifacts without touching
# the default tuned-HI build:
#
#   make -f Makefile.pro
#   make -f Makefile.pro verify
#   make -f Makefile.pro pro-clean
PRO := 1
include Makefile.pvsnes
