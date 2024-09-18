# src/utils.py

def ask_user_to_continue():
    """
    Asks the user if they want to continue or stop.

    Returns:
        None
    """
    user_input = input("Would you like to continue to the next stage? (y/n): ")

    while True:
        if user_input.lower() == "n":
            print("Stopping the program.")
            quit()
        elif user_input.lower() == "y":
            print("Continuing to the next stage.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            user_input = input("Would you like to continue to the processing stage? (y/n): ")
