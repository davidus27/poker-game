def roundWinners(names):
    """
    Shows the winner(s)

    :index: TODO
    :returns: TODO

    """
    if len(names) == 1:
        print("The winner is ",names[0])
    else:
        print("Winners are: ", end="")
        for name in names:
            print(name, ", ",end="")
        print()

def allInOrFold():
    """
    The warning that player can only go allin or fold
    :returns: TODO

    """
    while True:
        print("Choose your option:")
        print("\t1) Fold")
        print("\t2) All-in")
        print("\t0) Exit")
        print("[0-2]")
        try:
            reply = int(input(">")) % 3
            return reply + 3 if reply > 0 else reply
        except:
            print("You need to put number.")

def optionsInput():
        """
        Decorator
        Prints out the options of the player

        :returns: users option as a number

        """
        while True:
            print("Choose your option:")
            print("\t1) Check")
            print("\t2) Call")
            print("\t3) Raise")
            print("\t4) Fold")
            print("\t5) All-in")
            print("\t0) Exit")
            print("[0-5]")
            try:
                return int(input(">")) % 6
            except:
                print("You need to put number.")


