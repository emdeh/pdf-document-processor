import os
import shutil
import yaml

def create_folders():
    """
    Prompts the user to input the name of a statement set and creates the necessary folders for processing the files.

    Returns:
        new_folder (str): The path of the newly created folder.
        ready_for_analysis (str): The path of the 'split-files' folder within the new folder.
        manual_splitting_folder (str): The path of the 'manual-splitting required' folder within the new folder.
        analysed_files_folder (str): The path of the 'analysed-files' folder within the new folder.
    """

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
    Moves a document file to the specified analysed files folder.

    Args:
        document_path (str): The path of the document file to be moved.
        analysed_files_folder (str): The path of the folder where the document file will be moved to.

    Returns:
        None

    Raises:
        FileNotFoundError: If the document file does not exist.
        PermissionError: If there is a permission error while moving the file.
    """

    print(f"Moving {os.path.basename(document_path)} to the analysed-files folder.\n")
    # Construct the destination path
    destination_path = os.path.join(analysed_files_folder, os.path.basename(document_path))

    # Move the file to the destination path
    shutil.move(document_path, destination_path)

    # Print a message indicating that the file has been moved
    print(f"Moved {os.path.basename(document_path)} to {os.path.basename(analysed_files_folder)}.\n")

def load_statement_config(config_path):
    """
    Loads the statement configuration from a YAML file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: The loaded configuration.

    Raises:
        FileNotFoundError: If the configuration file is not found at the given path.
    """
    
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}.")
    
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config

def select_statement_type(config):
    """
    Prompts the user to select a statement type from the provided configuration.

    Args:
        config (dict): The configuration containing a list of statement types.

    Returns:
        tuple: A tuple containing the selected statement type and its corresponding environment variable.

    Raises:
        None

    Example:
        >>> config = {
        ...     "statement_types": [
        ...         {"type_name": "Type A", "env_var": "ENV_VAR_A"},
        ...         {"type_name": "Type B", "env_var": "ENV_VAR_B"},
        ...         {"type_name": "Type C", "env_var": "ENV_VAR_C"}
        ...     ]
        ... }
        >>> select_statement_type(config)
        Available Statement Types:
        1. Type A
        2. Type B
        3. Type C
        Select a statement type (number): 2
        Selected statement type: Type B
        ({'type_name': 'Type B', 'env_var': 'ENV_VAR_B'}, 'ENV_VAR_B')
    """
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
                selected_type = config["statement_types"][selection - 1]
                print(f"Selected statement type: {selected_type['type_name']}")
                return selected_type, selected_type['env_var']  # Adjust for zero-based index   
            else:
                print("Invalid selection. Please select a number from the list.")
        except ValueError:
            print("Please enter a number.")

def set_model_id(selected_env_var):
    """
    Sets the MODEL_ID environment variable based on the selected statement type.

    Args:
        selected_env_var (str): The selected statement type.

    Returns:
        str: The value of the MODEL_ID environment variable.

    Raises:
        SystemExit: If no corresponding MODEL ID variable is found for the selected statement type.
    """
    model_id = os.getenv(selected_env_var)
    if model_id:
        os.environ["MODEL_ID"] = model_id
        print(f"MODEL ID set to: {model_id}")
        return model_id
    else:
        print(f"No corresponding MODEL ID variable found for {selected_env_var}.\nQuitting program.")
        quit()

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