******************************************************
**                                                  **
**             Realistic Pathfinding                **
**                                                  **
**   Pathing.exe:  Sample program to accompany      **
**                 article.  Allows you to test     **
**                 a variety of pathfinding and     **
**                 smoothing techniques, and        **
**                 profile / time them.             **
**                                                  **
**       by Marco Pinter, (c) 2000                  **
**                                                  **
******************************************************

Installation:  Simply copy the executable (Pathing.exe)
               and the accompanying *.bmp files into
               any directory.

Source Code:   The core pathfinding source, path.cpp 
               and path.h, is also provided.  Note that 
               the source is not fully polished or fully 
               commented.  My apologies for any confusion.

FEATURES:

 <The Grid>:  
   When the toggle in the upper right is set to
   "Set Blockers", clicking and dragging on the grid
   will toggle blocking tiles.  (A blocked tile is displayed
   in black, while a free tile is in white.)  You cannot
   toggle the tile containing the ship.

   When the toggle in the upper right is set to
   "Run Path", clicking a tile on the grid will initiate
   a pathfind to that tile.  If the pathfind was not able
   to find a route, the ship will not move.

 [Initial checkboxes]:
   <Use Curves>: When on, the program incorporates the
                 turning radius into curved turns.  When
                 off, all turns are angular.
   <Smooth-48>:  When on, the "pre-smoothing" algorithm
                 is conducted.
   <Smooth-simple>:  When on, the simple smoothing pass 
                     is conducted.
   <Ignore Bounds>:  When on, the search can be conducted
                     outside the 30x30 bounds of the screen
                     grid.  This allows a more accurate
                     measurement of performance, though it
                     can also result in paths that travel
                     outside the visible bounds.

 [Scrolling values]: 
   <Grid Size>:   The size of the visible grid on which the
                  search will take place.  Max 30x30.
   <Object Size>: The size of the object (the ship), in 
                  tile units.  Note that values of 1.0 or
                  greater will require more than 1 tile
                  distance between blockers.
   <Speed>:       Speed at which ship will travel along path
                  (does not affect pathfinding algorithms.)
   <Search Adjacent>:  How many adjacent tiles will be 
                  searched at each node (4,8,24,48).
   <Granularity>: The granularity used when "walking" curves,
                  in both the simple smoothing pass, and the
                  Directional A* search (but only on the origin
                  node of that search.)
   <Turn Radius>: Turning radius of the ship, in tile units.

[Ship Info]:
   <Position>:    Moves the starting position of the ship.
   <Rotation>:    Changes the starting rotation of the ship,
                  in units of 1/16th of a circle.
   <Origin/Current>:  Toggles between "Origin", where all 
                  searches will revert back to the current
                  ship's origin point, or "Current", which
                  will start searches from ship's current
                  location.
                  ***NOTE that you can initiate searches at
                  any time during a search, so if the toggle
                  is on "Current", you can change goals 
                  repeatedly to simulate actual gameplay 
                  conditions.

[Additional checkboxes]:
   <Directional Search>:  Search will be "Directional".
   <Fixed Angles>:        Paths will be constrained to
                          16 angles only.

[Path Computation]:
   Displays the calculation time of the last path computation.

[Hybrid]:
   Sets the special "Hybrid" mode of searching & smoothing.


Note that some options are incompatible with others, so certain
checkboxes may disable others, and/or limit the range of certain
scrolling values.
