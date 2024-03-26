import os

def create_folders():
    # Prompt the user to input the name of the statement set
    statement_set_name = input("Enter the name of the statement set: ")

    # Create a folder based on the statement set name
    base_folder = os.getenv("INITIAL_INPUT_FOLDER")
    new_folder = os.path.join(base_folder, statement_set_name)
    os.makedirs(new_folder)
    print(f"Created {os.path.basename(new_folder)} to hold processed files.\n")
    
    # Create the 'split-files' folder within the new folder
    split_files_folder = os.path.join(new_folder, 'split-files')
    os.makedirs(split_files_folder)
    print(f"Created {os.path.basename(split_files_folder)} to hold successfully split files.\n")
    
    # Create the 'manual-splitting required' folder within the new folder
    manual_splitting_folder = os.path.join(new_folder, 'manual-splitting required')
    os.makedirs(manual_splitting_folder)
    print(f"Created {os.path.basename(manual_splitting_folder)} to hold files that fail auto-splitting.\n")

    return new_folder, split_files_folder, manual_splitting_folder