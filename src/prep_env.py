import os

def create_folders():
    while True:
        # Prompt the user to input the name of the statement set
        statement_set_name = input("Enter the name of the statement set: ")

        # Create a folder based on the statement set name
        base_folder = os.getenv("INITIAL_INPUT_FOLDER")
        new_folder = os.path.join(base_folder, statement_set_name)

        # Check if the folder already exists
        if os.path.exists(new_folder):
            # Folder already exists, prompt user for confirmation
            user_input = input(f"The folder '{os.path.basename(statement_set_name)}' already exists. Do you want to use this folder? (yes/no): ")
            if user_input.lower() == 'yes':
                # User wants to use the existing folder
                print(f"Using existing folder '{os.path.basename(statement_set_name)}' to hold processed files.\n")
                break
            elif user_input.lower() == 'no':
                # User wants to enter a new folder name
                print("Please enter a different name.")
                continue
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")
                continue
        else:
            # Folder doesn't exist, create it
            os.makedirs(new_folder)
            print(f"Created '{os.path.basename(statement_set_name)}' to hold processed files.\n")
            break
    
    # Create the 'split-files' folder within the new folder
    split_files_folder = os.path.join(new_folder, 'split-files')
    os.makedirs(split_files_folder)
    print(f"Created 'split-files' folder to hold successfully split files.\n")
    
    # Create the 'manual-splitting required' folder within the new folder
    manual_splitting_folder = os.path.join(new_folder, 'manual-splitting required')
    os.makedirs(manual_splitting_folder)
    print(f"Created 'manual-splitting required' folder to hold files that fail auto-splitting.\n")

    return new_folder, split_files_folder, manual_splitting_folder