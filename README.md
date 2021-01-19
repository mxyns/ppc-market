# ppc-market
# PPC - Project - Market
Python interprocess communication / multiprocessing / multithreading project
Energy market simulation with clients, weather parameters and external factors such as wars, tensions, etc.

## Running
unix system :
`python3 ./main.py [silent] [max_turns_count]`

windows (requires wsl2) :
`wsl`
`python3 ./main.py [silent] [max_turns_count]`

Parameters :
* `silent` hides the houses thought process which can be quite annoying considering the quantity of messages sent by each home
* `max_turns_count` (replace by a integer) maximum time the market will go to. after that market will stop (houses and weather source won't)

## More
* `TU` means Time Unit
* `MU` means Money Unit
* `EU` means Energy Unit
* A home's positive energy count displayed is an excess that has been sold, hence the positive money amount displayed (money gained by the house)