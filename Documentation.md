0# Documentation for PDF Processing and Data Extraction System

This system processes financial statements in PDF format, extracts information using custom Microsoft Document Intelligence models, and writes the extracted data to an Excel file. The program is structured around a series of Python scripts within a `src` directory, complemented by a configuration file and requires a virtual environment for dependencies management.

## System Overview

The process flow involves several key steps:

1. **Environment Setup**: Initialisation of environment variables and creation of necessary folders for file processing.
2. **PDF Processing**: Counting and processing of PDF files including splitting based on defined criteria.
3. **Data Extraction**: Utilising custom Document Intelligence models to analyse text and structure in processed PDFs.
4. **Data Transformation**: Extracting and formatting data from analysis results for summary and transactional data.
5. **Output Generation**: Writing the extracted data to an Excel file for further analysis or storage.

## Files and Their Functions

### `azure_blobs_utils.py` ###

Provides ultility functions for interaction with Azure Blob Storage.

- **`get_blob_service_client()`**: Retrieves the Blob Service Client.
- **`list_blobs()`**: Lists blobs in a container.
- **`read_blob_content()`**: Reads and outputs the contents of a blob.
- **`upload_analysis_results_to_blob()`**: Uploads the analysis results to Azure Blob Storage as a JSON file.

### `count_pdfs.py`

Provides utilities for counting PDFs and their pages before and after processing, aiding in validation processes.

- **`count_pdf_pages()`**: Counts the pages in a single PDF.
- **`process_pdf_count()`**: Aggregates file and page counts across a set of folders.
- **`save_to_excel()`**: Writes detailed and summary page count data to an Excel file.

### `csv_utils.py`

Handles the extraction, transformation, and formatting of data from the analysis results.

- **`extract_static_info()`**: Extracts static information relevant across all documents of a certain type.
- **`process_transactions()`**: Processes dynamic transactional data from documents.
- **`convert_amount()`**: Converts numerical values in strings into a float type.
- **`extract_and_process_summary_info()`**: Extracts and formats summary information from document analysis results.
- **`format_summary_for_excel()`**: Flattens the dictionary output from `extract_and_process_summary_info()`.
- **`write_transactions_and_summaries_to_excel()`**: Writes formatted transaction and summary data to an Excel file.
- **`write_raw_data_to_excel()`**: Writes raw extracted text data to an excel file.

### `doc_ai_utils.py`

Interfaces with the Azure Document Analysis Client for document analysis.

- **`initialise_analysis_client()`**: Sets up the Document Analysis Client with necessary credentials.
- **`analyse_document()`**: Analyses a document using the specified model, extracting structured data.
- **`analyse_layout_document()`**: Analyses a document using a pre-built layout model.
- **`extract_table_data()`**: Extracts table data from the layout and structures it into rows.
- **`extract_all_text()`**: Extracts all text content from the PDFs.

### `pdf_processor.py`

Contains functions for PDF manipulation, including counting pages and splitting documents based on content patterns.

- **`find_document_starts()`**: Scans a PDF for document start patterns, returning their page numbers.
- **`split_pdf()`**: Splits a PDF into separate documents based on start patterns.
- **`process_all_pdfs()`**: Orchestrates the scanning and splitting of PDFs within a folder, handling single and multiple document PDFs.
- **`get_config_for_type()`**: Retrieves the configuration for a specific statement type.
- **`find_statement_starts()`**: Identifies the starting pages of statements within a PDF file.
- **`is_pdf_machine_readable()`**: Checks a PDF to determine if it is machine-readable.
- **`extract_text_from_page()`**: Extracts the text from a PDF, using OCR extraction if specified.

### `postprocess_utils.py` ###

Two classes that are ultilised by the `postprocess.py` script. Each have a list of tasks that can readily called.

- **`ExcelHandler`**: A class to handle the reading and writing of excel files.
    - **`fill_missing_dates()`**: Fills the missing dates within the "Date" column via the forward-fill method.

- **`PDFPostProcessor`**: A class to handle the post-processing of seperated PDF files.
    - **`categorise_by_value()`**: Categorise PDF statements into folders and apply a prefix to the filenames according to a user specified criteria.
    - **`add_date_prefix_to_filenames()`**: Adds the statement start date prefix to PDF filenames.
    - **`identify_and_move_duplicates()`**: Identifies duplicate statements and moves them into a duplicates folder.

### `postprocess.py` ###

Allows the user to apply several post-processing pipelines to a folder of seperated PDFs according to the classes defined in `postprocess_utils.py`.

- **`main()`**: Accepts two arguments; `--input` and `--tasks`. Input is the path to the folder containing the target excel or PDFs. Tasks specifies which post-processing pipeline is applied to the input.

### `prep_env.py`

Responsible for environment preparation tasks including directories creation and configuration loading.

- **`create_folders()`**: Prompts the user for a statement set name, creating structured directories for file processing stages.
- **`move_analysed_file()`**: Moves processed files to a designated folder post-analysis.
- **`load_statement_config()`**: Loads statement processing configuration from a YAML file.
- **`select_statement_type()`**: Enables user selection of statement type for processing, as defiend in the YAML configuration file. 
- **`set_model_id()`**: Sets the model id to designated model type.
- **`copy_files()`**: Copies the source folder PDF files to the destination folder.

### `preprocess.py` ###

This script allows the user to input a single PDF of multiple statements and outputs a folder of PDFs split down to individual statements. Most of the `process.py` and `postprocess.py` inputs use the outputs from this script.

- **`main()`**: Accepts three arguments; `--input`, `--name`, `--type`. Input is the path to the PDF/s. Name specifies the output folder's name. Type is the specific kind of statement found in the PDF. See `config/type_models.yaml` for the list of options.

### `process.py` ###

This script takes a folder of seperated PDFs, as per the output of `preprocess.py`, extracts the data in each, sorts and writes it to an excel file.

- **`main()`**: Accepts three arguments; `--input`, `--config_type`, `--type`. Input is the path to the folder containing the PDF/s, and is typically the output from `preprocess.py`. Config Type is an optional argument that allows a user to provide a custom list of file types to process. The default provided list is `config/type_models.yaml`. Type is the specific kind of statement found in the PDF and is found in the list seen within the yaml file provided to the Config Type argument.

### `raw_process.py` ###

This script functions very similarly to `process.py`, however the output is raw un-sorted text data. This is a quick alternative if an untrained type is discovered and a type yaml has yet to be created.

- **`main()`**: Accepts only one argument: `--input`. Input is the path to the folder containing the PDF/s and is typically the output from `preprocess.py`. 

### `utils.py` ###

A simple script that asks the user if they want to continue or stop.

- **`ask_user_to_continue()`**: Asks the user if they wish to continue to the next stage of the program.

### `config` (`type_models.yaml`)

Defines the structure and fields of interest for different statement types, influencing data extraction logic. Each type references a pre-trained custom extraction model.

## System Dependencies

Managed via a `requirements.txt` file at the root of the project, including packages such as `fitz` (PyMuPDF), `pandas`, `azure.ai.formrecognizer`, `python-dotenv`, and `PyYAML`.

## Data Flow Example

Here's a simplified example of data transformation through the pipeline:

1. **PDF Processing**: Splits a PDF named `MonthlyStatement.pdf` into two separate documents based on the start pattern.
2. **Document Analysis**: Extracts data from each split document, identifying fields like `Transaction Date`, `Description`, and `Amount`.
3. **Data Transformation**:

```python
   transactions = [
       {"Date": "2023-04-01", "Description": "Grocery

 Purchase", "Amount": "$150.00"},
       {"Date": "2023-04-03", "Description": "Online Subscription", "Amount": "$12.99"}
   ]
```

4. **Output Generation**: Writes the above transactions to an Excel file, maintaining the structure and providing insights into financial activities.

## Conclusion


TO-DO: Expan on data flow example to describe how data is stored and flattened for writing to excel

Need to update