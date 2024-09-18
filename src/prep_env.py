# src/prep_env.py

import os
import shutil
import yaml


class EnvironmentPrep:
    def __init__(self):
        self.config = None

    def create_folders(self):
        """
        Prompts the user to input the name of a statement set and creates the necessary folders for processing the files.

        Returns:
            new_folder (str): The path of the newly created folder.
            ready_for_analysis (str): The path of the 'split-files' folder within the new folder.
            manual_splitting_folder (str): The path of the 'manual-splitting required' folder within the new folder.
            analysed_files_folder (str): The path of the 'analysed-files' folder within the new folder.
        """
        while True:
            statement_set_name = input("Enter the name of the statement set: ")

            base_folder = os.getenv("INITIAL_INPUT_FOLDER")
            new_folder = os.path.join(base_folder, statement_set_name)

            if os.path.exists(new_folder):
                user_input = input(
                    f"The folder '{os.path.basename(statement_set_name)}' already exists. Do you want to use this folder? (yes/no): "
                )
                if user_input.lower() == "yes":
                    print(
                        f"Using existing folder '{os.path.basename(statement_set_name)}' to hold processed files.\n"
                    )
                    break
                elif user_input.lower() == "no":
                    print("Please enter a different name.")
                    continue
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.")
                    continue
            else:
                os.makedirs(new_folder)
                print(f"Created '{os.path.basename(statement_set_name)}' to hold processed files.\n")
                break

        ready_for_analysis = os.path.join(new_folder, "split-files")
        if not os.path.exists(ready_for_analysis):
            os.makedirs(ready_for_analysis)
            print("Created 'split-files' folder to hold files ready for analysis.\n")
        else:
            print(
                "The 'split-files' folder already exists. Using existing folder to hold files ready for analysis.\n"
            )

        manual_splitting_folder = os.path.join(new_folder, "manual-splitting required")
        if not os.path.exists(manual_splitting_folder):
            os.makedirs(manual_splitting_folder)
            print(
                "Created 'manual-splitting required' folder to hold files that fail auto-splitting.\n"
            )
        else:
            print(
                "The 'manual-splitting required' folder already exists. Using existing folder to hold files that fail auto-splitting.\n"
            )

        analysed_files_folder = os.path.join(new_folder, "analysed-files")
        if not os.path.exists(analysed_files_folder):
            os.makedirs(analysed_files_folder)
            print("Created 'analysed-files' folder to hold files that have been analysed.\n")
        else:
            print(
                "The 'analysed-files' folder already exists. Using existing folder to hold analysed files.\n"
            )

        return new_folder, ready_for_analysis, manual_splitting_folder, analysed_files_folder

    def move_analysed_file(self, document_path, analysed_files_folder):
        """
        Moves a document file to the specified analysed files folder.

        Args:
            document_path (str): The path of the document file to be moved.
            analysed_files_folder (str): The path of the folder where the document file will be moved to.
        """
        print(f"Moving {os.path.basename(document_path)} to the analysed-files folder.\n")
        destination_path = os.path.join(analysed_files_folder, os.path.basename(document_path))
        shutil.move(document_path, destination_path)
        print(f"Moved {os.path.basename(document_path)} to {os.path.basename(analysed_files_folder)}.\n")

    def load_statement_config(self, config_path):
        """
        Loads the statement configuration from a YAML file.

        Args:
            config_path (str): The path to the configuration file.

        Raises:
            FileNotFoundError: If the configuration file is not found at the given path.
        """
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}.")

        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)

    def select_statement_type(self):
        """
        Prompts the user to select a statement type from the provided configuration.

        Returns:
            tuple: A tuple containing the selected statement type and its corresponding environment variable.
        """
        if not self.config:
            raise ValueError("Configuration not loaded.")

        type_names = [stype["type_name"] for stype in self.config["statement_types"]]

        print("Available Statement Types:")
        for i, type_name in enumerate(type_names, start=1):
            print(f"{i}. {type_name}")

        while True:
            try:
                selection = int(input("Select a statement type (number): "))
                if 1 <= selection <= len(type_names):
                    selected_type = self.config["statement_types"][selection - 1]
                    print(f"Selected statement type: {selected_type['type_name']}")
                    return selected_type, selected_type["env_var"]
                else:
                    print("Invalid selection. Please select a number from the list.")
            except ValueError:
                print("Please enter a number.")

    def set_model_id(self, selected_env_var):
        """
        Sets the MODEL_ID environment variable based on the selected statement type.

        Args:
            selected_env_var (str): The selected statement type.

        Returns:
            str: The value of the MODEL_ID environment variable.
        """
        model_id = os.getenv(selected_env_var)
        if model_id:
            os.environ["MODEL_ID"] = model_id
            print(f"MODEL ID set to: {model_id}")
            return model_id
        else:
            print(f"No corresponding MODEL ID variable found for {selected_env_var}.\nQuitting program.")
            quit()

    def copy_files(self, source_folder, destination_folder):
        """
        Copies files from the source folder to the destination folder.

        Args:
            source_folder (str): The path of the source folder.
            destination_folder (str): The path of the destination folder.
        """
        print(f"Copying files from {source_folder} to {destination_folder}...\n")
        for filename in os.listdir(source_folder):
            source_path = os.path.join(source_folder, filename)
            dest_path = os.path.join(destination_folder, filename)
            if os.path.isfile(source_path):
                shutil.copy(source_path, dest_path)
        print("Files copied successfully.\n")
