### The BIGMACC Project

The ETA Lab at UBC is studying the impacts of various decarbonization and climate change adaption strategies within the 
built environment. We are building out a module within the CEA to iteratively simulate building energy demand of several
sections of municipalities chosen for their representation as exemplars for climate change impacts. The entirety of simulations
will cover the exhaustive combination and isolation of roughly one dozen strategies aimed at mitigation and adaptation.

We are contributing a single script to the CEA that will iterate through a list of scenarios stored in a directory built
outside of the CEA. The directory will contain a list of binary keys (e.g. 1001101), where a "1" or "0" relate to the 
presence of a single strategy within the simulation. The script will move through the directory, creating new scenarios 
on the fly based on a typology and zone file contained within each directory. Results of the demand, LCA, potentials, 
and a custom impact analysis will be saved within the strategy directory before the script moves onto creating, assessing,
and writing the next stategy set. 