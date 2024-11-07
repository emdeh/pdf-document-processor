# pdf-document-processor
env file requirements

```bash
# INITIAL_INPUT_FOLDER=
# CONFIG_PATH
# MODEL_ENDPOINT=
# MODEL_API_KEY=
# MODEL_ID_<DOC-TYPE-BASED-ON-YAML>=
# MODEL_ID_AMEX_CARD=<enter-model-id-here>

```

# PDF Document Processor

This project consists of 4 main scripts designed to preprocess PDF documents and extract data from them using Azure Document Intelligence (formerly Form Recognizer). 
The preprocessing script splits PDFs and prepares them for analysis. 
The processing and raw processing scripts extract data and write it to an Excel file, either as treated or raw data respectively.
The postprocessing script offers several data treatment pipelines that allow for more detailed analysis.


## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Preprocessing Script](#preprocessing-script)
  - [Processing Script](#processing-script)
  - [Raw Processing Script](#rawprocessing-script)
  - [Postprocessing Script](#postprocessing-script)
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

- **Raw Processing:**
  - Extracts data from PDFs using Azure Document Intelligence.
  - Supports custom models specified in a YAML configuration file.
  - Writes extracted raw data to Excel files with no formatting.

- **Postprocessing:**
  - Allows for several different kinds of data treating pipelines for improved data analytics.
  - *Excel Handler:*
    - Fill Missing Dates from known date values.
  - *PDF Postprocessor:*
    - Categorise by user specified value.
    - Add date prefix to filenames.
    - Identify and remove duplicates.

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

- `--input` OR `-i`: Path to the folder containing the original PDFs.
- `--name` OR `-n`: Name of folder the output will be generated into.
- `--type` OR `-t`: Type of file to process. See `/config/type_models.yaml` for options.

#### Example Usage

```bash
python preprocess.py \
  -i /path/to/original_pdfs \
  -n "Test Run" \
  -t "AMEX - Card Statement"
  ```

### Processing Script
The processing script (`process.py`) extracts data from PDFs, sorts it according to what kind of data it is, and writes it to an Excel file.

Command-Line Arguments
- `--input` OR `-i`: Path to the folder containing the PDFs to process (output from preprocessing).
- `--config_type` OR `-c`: Path to the YAML configuration file specifying statement types. Defaults to `/config/type_models.yaml`
- `--type` OR `-t`: Name of the statement type to use (as specified in the YAML file).

#### Example Usage

```bash
python process.py \
  -i /path/to/preprocessed_pdfs \
  -t "Your Statement Type Name"
```

### Raw Processing Script
The raw processing script (`rawprocess.py`) functions similarly to `process.py`, except the output is raw data instead of processed and partially sorted data.

Command-Line Arguments
- `--input` OR `-i`: Path to the folder containing the PDFs to process (output from `preprocessing`).

#### Example Usage

```bash
python rawprocess.py \
  -i /path/to/preprocessed_pdfs
```

### Post Processing Script
The post processing script (`postprocess.py`) allows the user to apply one or more types of post processing pipelines to a folder of PDFs created from the output of `preprocess.py`.

Command-Line Arguements
- `--input` OR `-i`: Path to the folder containing the PDFs to process (output from `preprocessing.py`)
- `--tasks` OR `-t`: The task that will be applied to the input. The list of available tasks is contained with the help function, and also listed below.

#### Task Options
- "fill_missing_dates":
  - Fills missing dates in the output Excel Date column via back-fill propagation
- "categorise_by_value":
  - Categorises the pdfs by a user specified value. Appends value to filename and moves PDFs into folders of the same value. Requests name and example of the value type.
- "add_date_prefix_to_filenames":
  - Appends a date prefix to the pdf filenames. Requests example of date format.
- "identify_and_move_duplicates":
  - Identifies duplicates and moves them into a duplicate folder. Requests examples of Account Number, Statement Number and Statement Start Date from user to create unique identifiers.

#### Example Usage

```bash
python postprocess.py \
  -i /path/to/preprocessed_pdfs \
  -t "Name of task to perform"
```

## Configuration
The processing script relies on a YAML configuration file (`type_models.yaml`) to define statement types and their corresponding models.

### Sample type_models.yaml

```bash
statement_types:
  - type_name: "Your Statement Type Name"
    env_var: "MODEL_ID_YOUR_STATEMENT_TYPE"
    start_pattern: 'Pattern Of Page Numbering'
    must_not_contain: "Exclusion phrase"
    start_phrase: "Target Phrase Here"
    split_type: "page_start OR start_end"
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

- `type_name`: Name of the statement type (used with --type).
- `env_var`: Environment variable name for the model ID.
- `start_pattern` : If specified, the method will apply this as a regex to identify the start of a statement.
- `must_not_contain` : Used in conjunction with start_pattern or start_phrase to assist with identifying the end of a statement.
- `start_phrase` : If specified, the method will apply this as a regex to identify the start of a statement.
- `split_type` : Normally set to "page_start", however if the "must_not_contain" value is defined, set this to "start_end".
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
- Your statement type is "ANZ - Bank Statement"
- You want to sort the pdfs by account number

#### Preprocess the PDFs:
```bash
python preprocess.py \
  -i /data/original_pdfs \
  -n "processed_pdfs"
  -t "ANZ - Bank Statement"
```

#### Process the PDFs:
```bash
python process.py \
  -i /data/processed_pdfs/split-files \
  -t "ANZ - Bank Statement"
```

#### Post process the PDFs:
```bash
python postprocess.py \
  -i /data/processed_pdfs/split-files \
  -t "categorise_by_value"
```
You would then be asked for the name of the value, e.g."Account" and then an example of the account number, e.g."44-1234"

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