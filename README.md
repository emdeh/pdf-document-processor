# pdf-document-processor
env file requirements

```
# INITIAL_INPUT_FOLDER=
# CONFIG_PATH
# MODEL_ENDPOINT=
# MODEL_API_KEY=
# MODEL_ID_<DOC-TYPE-BASED-ON-YAML>=
# MODEL_ID_AMEX_CARD=<enter-model-id-here>

```

# PDF Document Processor

This project consists of two main scripts designed to preprocess PDF documents and extract data from them using Azure Document Intelligence (formerly Form Recognizer). The preprocessing script splits PDFs and prepares them for analysis, while the processing script extracts data and writes it to an Excel file.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Preprocessing Script](#preprocessing-script)
  - [Processing Script](#processing-script)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Example](#example)
- [To-Do List](#to-do-list)
- [License](#license)

## Features

- **Preprocessing:**
  - Splits multipage PDFs into individual documents based on predefined patterns.
  - Counts pages before and after splitting and saves counts to Excel files.

- **Processing:**
  - Extracts data from PDFs using Azure Document Intelligence.
  - Supports custom models specified in a YAML configuration file.
  - Writes extracted data to Excel files with appropriate formatting.

## Prerequisites

- Python 3.7 or higher
- Azure account with Document Intelligence resource
- Required Python packages (see [Installation](#installation))

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/pdf-document-processor.git
    cd pdf-document-processor
    ```

2. **Create a virtual environment and activate it:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the `.env` file:**

    Create a `.env` file in the root directory and add the following environment variables:

    ```dotenv
    MODEL_ENDPOINT=https://your-model-endpoint.cognitiveservices.azure.com/
    MODEL_API_KEY=your_api_key
    MODEL_ID_YOUR_STATEMENT_TYPE=your_model_id
    ```

    Replace the placeholders with your actual Azure endpoint, API key, and model IDs.

## Usage

### Preprocessing Script

The preprocessing script (`preprocess.py`) splits PDFs and prepares them for analysis.

#### Command-Line Arguments

- `--input_folder`: Path to the folder containing the original PDFs.
- `--output_folder`: Path where the split PDFs and counts will be saved.
- `--statement_set_name`: Name to identify the statement set.

#### Example Usage

```bash
python preprocess.py \
  --input_folder /path/to/original_pdfs \
  --output_folder /path/to/output_folder \
  --statement_set_name my_statements
  ```

### Processing Script
The processing script (`process.py`) extracts data from PDFs and writes it to an Excel file.

Command-Line Arguments
- `--input_folder`: Path to the folder containing the PDFs to process (output from preprocessing).
- `--output_folder`: Path where the results (Excel files) will be saved.
- `--config_path`: Path to the YAML configuration file specifying statement types.
- `--statement_type_name`: Name of the statement type to use (as specified in the YAML file).

#### Example Usage

```bash
python process.py \
  --input_folder /path/to/preprocessed_pdfs \
  --output_folder /path/to/results_folder \
  --config_path config/type_models.yaml \
  --statement_type_name "Your Statement Type Name"
```

## Configuration
The processing script relies on a YAML configuration file (type_models.yaml) to define statement types and their corresponding models.

### Sample type_models.yaml

```bash
statement_types:
  - type_name: "Your Statement Type Name"
    env_var: "MODEL_ID_YOUR_STATEMENT_TYPE"
    transaction_dynamic_fields:
      - field_name: "TransactionDate"
        is_date: true
      - field_name: "Amount"
        is_amount: true
    transaction_static_fields:
      - field_name: "AccountNumber"
    summary_fields:
      - field_name: "TotalBalance"
        is_amount: true
```

- `type_name`: Name of the statement type (used with --statement_type_name).
- `env_var`: Environment variable name for the model ID.
- `transaction_dynamic_fields`: Fields to extract from transactions.
- `transaction_static_fields`: Static fields to extract from the document.
- `summary_fields`: Summary fields to extract.

## Environment Variables
Set the following environment variables in your .env file or environment:

- `MODEL_ENDPOINT`: Your Azure Document Intelligence endpoint.
- `MODEL_API_KEY`: Your Azure API key.
- Model IDs for each statement type, using the env_var specified in the YAML configuration.

### Example
Assuming you have:

- Original PDFs in `/data/original_pdfs`
- You want to output preprocessed files to `/data/processed_pdfs`
- Your statement type is "Bank Statement"

#### Preprocess the PDFs:
```bash
python preprocess.py \
  --input_folder /data/original_pdfs \
  --output_folder /data/processed_pdfs \
  --statement_set_name bank_statements
```

#### Process the PDFs:
```bash
python process.py \
  --input_folder /data/processed_pdfs/split-files \
  --output_folder /data/results \
  --config_path config/type_models.yaml \
  --statement_type_name "Bank Statement"
```

## To-Do List

### Implement Error Logging:
- Add logging throughout the scripts to capture errors and important events.
- Use Python's logging module to create logs at different levels (INFO, DEBUG, ERROR).
- Write logs to a file for later review.

### Improve CLI Output:
- Enhance the command-line interface (CLI) output for both scripts.
- Use clear and informative messages to indicate progress and any issues.
- Consider adding a verbose mode for more detailed output.

### Refine Folder Structure:
- Tidy up how folders are created and managed.
- Ensure that all output directories are created if they do not exist.
- Allow users to specify custom folder names and paths.
- Clean up temporary files and directories after processing.

### Dockerize the Application:

- Create a Dockerfile to containerize the application.
- Simplify deployment and ensure consistency across environments.

### Implement Configuration Validation:
- Validate the YAML configuration file before processing.

### Check for missing fields or incorrect formats.
 
### Optimize Performance:
- Investigate ways to improve the processing speed.
- Consider parallel processing of PDFs if appropriate.

### Handling scenarios where transaction dates are already fully provided

To handle scenarios where some statement types have transaction dates that already include the year, while others have partial dates (without the year).

To achieve this flexibility, need to update the YAML configuration and the relevant methods in your CSVUtils class to allow the system to intelligently determine whether to append the year to transaction dates based on the presence of year information in the date format.

To the YAML:
- add an additional flag `has_year` for the transaction date field.
- This will indicate whether the transaction date includes the year
- values are `true` or `false`

In `assign_years_to_dates()`
- dtermine whether to assign the year based on the `has_year` flag

```