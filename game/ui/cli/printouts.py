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
