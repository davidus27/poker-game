# pokerGame
Texas Hold'em poker is easy terminal game written in Python for educational purposes.


## Table of contents
* [Introduction](#Introduction)
* [Installation](#Installation)
* [Rules](#Rules)
* [Testing](#Testing)
* [TODO list](#TODO)
* [UML](#UML)
* [License](#License)



## Introduction
Simple Poker game you can play in terminal or cmd prompt. 

## Installation
Here is the easy process to download and play the game
You need to clone the repo

``
$git clone https://github.com/davidus27/pokerGame
$cd pokerGame
$python3 game/main.py
``
# Linux 
For easier playing in terminal you just need to give the script permissions to execute:
``
cd pokerGame
chmod +x game/main.py
``
now you can create alias in your .bashrc file 

``
alias name='path-to-the-program/pokerGame/game/main.py'
``

# Windows
If you are using Windows and want the .exe file you just need to install requirements
``$ pip3 install -r requirements.txt``
and create executable file 
``$ pyinstaller game/main.py``
# 



or download git repo 

Program is written in Python 3.x so you can play it simply by typing:
$python3 

## Rules
It is very easy to play. 
After the start the game will ask questions for creation of your character.
On the first round your balance (money) and cards should be on the screen and you can play the game 
by navigating through the numbers.

## Testing
TODO

## TODO

- [x] Beta version of the game released
- [x] Refactoring the codebase
- [x] Working detection system of the hand values of individual players
- [x] Ante binding for begining of the game
- [x] Basic bots playing against the player
- [ ] Unit testing
- [ ] More advanced bots calculating strategy
- [ ] Fixing wrong calculations of high cards
- [ ] Changing order of players each round
- [ ] basic GUI options
- [ ] saving the game progress over time



## UML

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
