# Final-Project---Software-Carpentry

Authors: Steven Shi & Justin Lanan
Date: 12/19/2022

This program makes a movie from generated images as a form of biomimicry simulation. These images need a temporary folder to be stored,
so this folder pathway must be specified in the Main function. There are also knobs to change the size of the images,
but those are best left to the current default as the program can crash from memory shortages in this folder.

Default time steps is 999 for a 2 minute simulation video and cannot exceed this. User can change to a shorter simulation if desired.

There is still currently a bug where the ciliates can cross eachother and get stuck, but this does not stop the simulation from continuing to the end.
