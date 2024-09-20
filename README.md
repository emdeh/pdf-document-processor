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

### Delete redundant code:
- Clean up old code folder.

### Handling scenarios where transaction dates are already fully provided

To handle scenarios where some statement types have transaction dates that already include the year, while others have partial dates (without the year).

To achieve this flexibility, need to update the YAML configuration and the relevant methods in your CSVUtils class to allow the system to intelligently determine whether to append the year to transaction dates based on the presence of year information in the date format.

To the YAML:
- add an additional flag `has_year` for the transaction date field.
- This will indicate whether the transaction date includes the year
- values are `true` or `false`

In `assign_years_to_dates()`
- dtermine whether to assign the year based on the `has_year` flag

```python
def assign_years_to_dates(self, transactions_df, statement_start_date_str, statement_end_date_str, has_year=False):
    """
    Assigns years to dates that lack year information based on the statement period.

    Args:
        transactions_df (pd.DataFrame): The transactions DataFrame.
        statement_start_date_str (str): The statement start date as a string (e.g., '22 June 2022').
        statement_end_date_str (str): The statement end date as a string (e.g., '22 July 2023').
        has_year (bool): Indicates whether the transaction dates already include the year.

    Returns:
        pd.DataFrame: The updated transactions DataFrame with years assigned to dates.
    """
    if has_year:
        # If transaction dates already have the year, no need to assign
        self.logger.info("Transaction dates already include the year. Skipping year assignment.")
        return transactions_df

    # Parse the statement start and end dates
    statement_start_date = pd.to_datetime(statement_start_date_str, format='%d %B %Y', errors='coerce')
    statement_end_date = pd.to_datetime(statement_end_date_str, format='%d %B %Y', errors='coerce')

    if pd.isna(statement_start_date) or pd.isna(statement_end_date):
        raise ValueError("Statement start or end date is invalid.")

    # Get the years covered in the statement
    start_year = statement_start_date.year
    end_year = statement_end_date.year

    # Initialize the current year
    current_year = start_year
    previous_month = None
    dates_with_year = []

    # Ensure transactions are sorted by date
    transactions_df = transactions_df.sort_values(by='Date').reset_index(drop=True)

    # Iterate over the 'Date' column using .items() for compatibility
    for idx, date in transactions_df['Date'].items():
        if pd.isna(date):
            dates_with_year.append(pd.NaT)
            continue

        # Extract day and month from the date
        day = date.day
        month = date.month

        # Detect year rollover
        if previous_month and month < previous_month:
            current_year += 1
            if current_year > end_year:
                current_year = end_year  # Prevent exceeding the end year

        # Create a new date with the assigned year
        try:
            new_date = pd.Timestamp(year=current_year, month=month, day=day)
        except ValueError:
            new_date = pd.NaT  # Handle invalid dates

        dates_with_year.append(new_date)
        previous_month = month

    # Assign the new dates to the DataFrame
    transactions_df['Date'] = dates_with_year

    # Debugging: Print a few rows to verify
    print("Transactions DataFrame after assigning years:\n", transactions_df.head())

    return transactions_df
```

in `write_transactions_and_summaries_to_excel()`L
- Determine whether the current statement type's transaction dates include the year using the `has_year` flag from the YAML configuration.
- Pass the `has_year` flag to the `assign_years_to_dates` method accordingly.

```python
def write_transactions_and_summaries_to_excel(
        self, transactions_records, summary_data, output_dir, excel_filename, table_data=None, statement_type=None
    ):
    # Create DataFrames from records
    transactions_df = pd.DataFrame(transactions_records)

    # Process summary data
    summary_rows = []
    for summary in summary_data:
        flattened_summary = self.format_summary_for_excel(summary)
        summary_rows.append(flattened_summary)

    summaryinfo_df = pd.DataFrame(summary_rows)

    # Debugging: Print summaryinfo_df columns and content
    print("Summary DataFrame columns:", summaryinfo_df.columns.tolist())
    print("Summary DataFrame content:\n", summaryinfo_df.head())

    # Initialize sets for amount and date columns
    amount_columns = set()
    date_columns = set()
    date_column_formats = {}  # Mapping from column names to date formats
    has_year_map = {}  # Mapping from column names to has_year flags

    # Extract field information from statement_type
    if statement_type:
        # Transaction Dynamic Fields
        for field in statement_type.get('transaction_dynamic_fields', []):
            field_name = field['field_name']
            if field.get('is_amount'):
                amount_columns.add(field_name)
            if field.get('is_date'):
                date_columns.add(field_name)
                date_format = field.get('date_format')
                if date_format:
                    date_column_formats[field_name] = date_format
                has_year = field.get('has_year', False)
                has_year_map[field_name] = has_year

        # Transaction Static Fields
        for field in statement_type.get('transaction_static_fields', []):
            field_name = field['field_name']
            if field.get('is_amount'):
                amount_columns.add(field_name)
            if field.get('is_date'):
                date_columns.add(field_name)
                date_format = field.get('date_format')
                if date_format:
                    date_column_formats[field_name] = date_format
                has_year = field.get('has_year', False)
                has_year_map[field_name] = has_year

        # Summary Fields
        for field in statement_type.get('summary_fields', []):
            field_name = field['field_name']
            if field.get('is_amount'):
                amount_columns.add(field_name)
            if field.get('is_date'):
                date_columns.add(field_name)
                date_format = field.get('date_format')
                if date_format:
                    date_column_formats[field_name] = date_format
                has_year = field.get('has_year', False)
                has_year_map[field_name] = has_year

    # Convert amount columns to numeric
    for col in amount_columns:
        if col in transactions_df.columns:
            transactions_df[col] = pd.to_numeric(transactions_df[col], errors='coerce')
        if col in summaryinfo_df.columns:
            summaryinfo_df[col] = pd.to_numeric(summaryinfo_df[col], errors='coerce')

    # Convert date columns to datetime
    for col in date_columns:
        date_format = date_column_formats.get(col)
        if col in transactions_df.columns:
            if date_format:
                if transactions_df[col].dtype == object:
                    transactions_df[col] = transactions_df[col].str.title()  # Convert to Title Case
                transactions_df[col] = pd.to_datetime(
                    transactions_df[col],
                    format=date_format,
                    errors='coerce',
                    dayfirst=True
                )
            else:
                transactions_df[col] = pd.to_datetime(
                    transactions_df[col],
                    errors='coerce',
                    dayfirst=True
                )
        if col in summaryinfo_df.columns:
            if date_format:
                if summaryinfo_df[col].dtype == object:
                    summaryinfo_df[col] = summaryinfo_df[col].str.title()  # Convert to Title Case
                summaryinfo_df[col] = pd.to_datetime(
                    summaryinfo_df[col],
                    format=date_format,
                    errors='coerce',
                    dayfirst=True
                )
            else:
                summaryinfo_df[col] = pd.to_datetime(
                    summaryinfo_df[col],
                    errors='coerce',
                    dayfirst=True
                )

    # Determine if year assignment is necessary per transaction date field
    if 'Date' in transactions_df.columns and 'Date' in has_year_map:
        has_year = has_year_map['Date']
        if not has_year:
            # Extract statement start and end dates from summaryinfo_df
            if 'StatementStartDate_Value' in summaryinfo_df.columns and 'StatementEndDate_Value' in summaryinfo_df.columns:
                statement_start_date_str = summaryinfo_df['StatementStartDate_Value'].dropna().iloc[0]
                statement_end_date_str = summaryinfo_df['StatementEndDate_Value'].dropna().iloc[0]
                print(f"Statement Start Date: {statement_start_date_str}")
                print(f"Statement End Date: {statement_end_date_str}")
            else:
                print("Warning: 'StatementStartDate_Value' or 'StatementEndDate_Value' is missing in the summary data.")
                statement_start_date_str = statement_end_date_str = None

            if statement_start_date_str and statement_end_date_str:
                # Ensure the dates are strings in the correct format
                if isinstance(statement_start_date_str, pd.Timestamp):
                    statement_start_date_str = statement_start_date_str.strftime('%d %B %Y')  # '%d %B %Y'
                elif isinstance(statement_start_date_str, str):
                    statement_start_date_str = statement_start_date_str.title()

                if isinstance(statement_end_date_str, pd.Timestamp):
                    statement_end_date_str = statement_end_date_str.strftime('%d %B %Y')  # '%d %B %Y'
                elif isinstance(statement_end_date_str, str):
                    statement_end_date_str = statement_end_date_str.title()

                try:
                    # Assign years to transaction dates
                    transactions_df = self.assign_years_to_dates(
                        transactions_df,
                        statement_start_date_str,
                        statement_end_date_str,
                        has_year=has_year
                    )
                except Exception as e:
                    print(f"Error assigning years to dates: {e}")
            else:
                print("Warning: Statement start or end date is missing or invalid. Unable to assign years to transaction dates.")
        else:
            print("Transaction dates already include the year. No year assignment needed.")

    # Define the output file path
    output_file_path = os.path.join(output_dir, excel_filename)

    # Write DataFrames to Excel with formatting
    with pd.ExcelWriter(
        output_file_path,
        engine='xlsxwriter',
        datetime_format='dd/mm/yyyy',
        date_format='dd/mm/yyyy'
    ) as writer:
        transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
        summaryinfo_df.to_excel(writer, sheet_name='Summary', index=False)

        # Access the workbook and sheets
        workbook = writer.book
        transactions_sheet = writer.sheets['Transactions']
        summary_sheet = writer.sheets['Summary']

        # Define formats
        money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        # Apply formats to Transactions sheet
        for idx, col in enumerate(transactions_df.columns):
            if col in amount_columns:
                transactions_sheet.set_column(idx, idx, None, money_fmt)
            elif col in date_columns:
                transactions_sheet.set_column(idx, idx, None, date_fmt)

        # Apply formats to Summary sheet
        for idx, col in enumerate(summaryinfo_df.columns):
            if col in amount_columns:
                summary_sheet.set_column(idx, idx, None, money_fmt)
            elif col in date_columns:
                summary_sheet.set_column(idx, idx, None, date_fmt)

    print(f"Data written to the file '{os.path.basename(excel_filename)}' in {os.path.basename(output_dir)}.\n")
```