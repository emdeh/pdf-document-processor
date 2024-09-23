# prep_env.py

import os
import shutil
import yaml

class EnvironmentPrep:
    def create_folders(self, statement_set_name, base_folder):
        """
        Creates the necessary folders for processing the files.

        Args:
            statement_set_name (str): Name of the statement set.
            base_folder (str): Base path where folders will be created.

        Returns:
            tuple: Paths of the newly created folders.
        """
        new_folder = os.path.join(base_folder, statement_set_name)
        os.makedirs(new_folder, exist_ok=True)
        print(f"Using folder '{os.path.basename(statement_set_name)}' to hold processed files.\n")

        ready_for_analysis = os.path.join(new_folder, 'split-files')
        os.makedirs(ready_for_analysis, exist_ok=True)
        print("Created 'split-files' folder to hold files ready for analysis.\n")

        manual_splitting_folder = os.path.join(new_folder, 'manual-splitting required')
        os.makedirs(manual_splitting_folder, exist_ok=True)
        print("Created 'manual-splitting required' folder to hold files that fail auto-splitting.\n")

        analysed_files_folder = os.path.join(new_folder, 'analysed-files')
        os.makedirs(analysed_files_folder, exist_ok=True)
        print("Created 'analysed-files' folder to hold files that have been analysed.\n")

        return new_folder, ready_for_analysis, manual_splitting_folder, analysed_files_folder

    def move_analysed_file(self, document_path, analysed_files_folder):
        """
        Moves a document file to the specified analysed files folder.

        Args:
            document_path (str): Path to the document to be moved.
            analysed_files_folder (str): Destination folder.
        """
        print(f"Moving {os.path.basename(document_path)} to the analysed-files folder.\n")
        destination_path = os.path.join(analysed_files_folder, os.path.basename(document_path))
        shutil.move(document_path, destination_path)
        print(f"Moved {os.path.basename(document_path)} to {os.path.basename(analysed_files_folder)}.\n")

    def load_statement_config(self, config_path):
        """
        Loads the statement configuration from a YAML file.

        Args:
            config_path (str): Path to the configuration YAML file.

        Returns:
            dict: Loaded configuration.
        """
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}.")

        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
        return self.config

    def select_statement_type(self, statement_type_name=None):
        """
        Selects the statement type from the configuration.

        Args:
            statement_type_name (str): Name of the statement type to select.

        Returns:
            tuple: Selected statement type and its corresponding environment variable.

        Raises:
            ValueError: If the statement type is not found in the configuration.
        """
        if not self.config:
            raise ValueError("Configuration not loaded.")

        if statement_type_name:
            for stype in self.config["statement_types"]:
                if stype["type_name"] == statement_type_name:
                    print(f"Selected statement type: {stype['type_name']}")
                    return stype, stype["env_var"]
            raise ValueError(f"Statement type '{statement_type_name}' not found in configuration.")
        else:
            raise ValueError("No statement_type_name provided.")

    def set_model_id(self, selected_env_var):
        """
        Sets the MODEL_ID based on the selected statement type.

        Args:
            selected_env_var (str): Environment variable name for the model ID.
            env_vars (dict): Dictionary of environment variables.

        Returns:
            str: The model ID.

        Raises:
            ValueError: If the model ID is not found in env_vars.
        """
        model_id = os.getenv(selected_env_var)
        if model_id:
            print(f"MODEL ID set to: {model_id}")
            return model_id
        else:
            raise ValueError(f"No corresponding MODEL ID variable found for {selected_env_var}.")
        
    def copy_files(self, source_folder, destination_folder):
        """
        Copies PDF files from the source folder to the destination folder.

        Args:
            source_folder (str): Source directory.
            destination_folder (str): Destination directory.
        """
        print(f"Copying files from {source_folder} to {destination_folder}...\n")
        for filename in os.listdir(source_folder):
            source_path = os.path.join(source_folder, filename)
            dest_path = os.path.join(destination_folder, filename)
            if os.path.isfile(source_path) and filename.lower().endswith('.pdf'):
                shutil.copy(source_path, dest_path)
        print("Files copied successfully.\n")
