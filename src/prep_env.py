import os
import shutil
import yaml

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
    ready_for_analysis = os.path.join(new_folder, 'split-files')
    if not os.path.exists(ready_for_analysis):
        os.makedirs(ready_for_analysis)
        print(f"Created 'ready-for-analysis' folder to hold successfully split files.\n")
    else:
        print(f"The 'ready-for-analysis' folder already exists. Using existing folder to hold split files.\n")
    
    # Create the 'manual-splitting required' folder within the new folder
    manual_splitting_folder = os.path.join(new_folder, 'manual-splitting required')
    if not os.path.exists(manual_splitting_folder):
        os.makedirs(manual_splitting_folder)
        print(f"Created 'manual-splitting required' folder to hold files that fail auto-splitting.\n")
    else:
        print(f"The 'manual-splitting required' folder already exists. Using existing folder to hold files that fail auto-splitting.\n")

    # Create the 'analysed-files' folder within the new folder
    analysed_files_folder = os.path.join(new_folder, 'analysed-files')
    if not os.path.exists(analysed_files_folder):
        os.makedirs(analysed_files_folder)
        print(f"Created 'analysed-files' folder to hold files that have been analysed.\n")
    else:
        print(f"The 'analysed-files' folder already exists. Using existing folder to hold analysed files.\n")

    return new_folder, ready_for_analysis, manual_splitting_folder, analysed_files_folder

def move_analysed_file(document_path, analysed_files_folder):
    """
    Move a file to the analysed files folder.

    Args:
    - document_path (str): Path to the document file.
    - analysed_files_folder (str): Path to the folder where the document will be moved.
    """
    print(f"Moving {os.path.basename(document_path)} to the analysed-files folder.\n")
    # Construct the destination path
    destination_path = os.path.join(analysed_files_folder, os.path.basename(document_path))

    # Move the file to the destination path
    shutil.move(document_path, destination_path)

    # Print a message indicating that the file has been moved
    print(f"Moved {os.path.basename(document_path)} to {os.path.basename(analysed_files_folder)}.\n")

def load_statement_config(config_path):
    # Check if the file exists at the given path
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}.")
    
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def select_statement_type(config):
    # Extracting the list of type names from the configuration
    type_names = [stype["type_name"] for stype in config["statement_types"]]
    
    # Displaying the options to the user
    print("Available Statement Types:")
    for i, type_name in enumerate(type_names, start=1):
        print(f"{i}. {type_name}")
    
    # Prompting user for selection
    while True:
        try:
            selection = int(input("Select a statement type (number): "))
            # Validate selection is within the correct range
            if 1 <= selection <= len(type_names):
                print(f"Selected statement type: {type_names[selection - 1]}")
                return config["statement_types"][selection - 1]  # Adjust for zero-based index   
            else:
                print("Invalid selection. Please select a number from the list.")
        except ValueError:
            print("Please enter a number.")