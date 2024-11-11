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

### `main.py`

This is the entry point of the program. It orchestrates the flow of operations including environment setup, PDF processing, document analysis, data extraction, and output generation.

- **Environment Variables Loading**: Utilises `dotenv` to load configuration from a `.env` file, setting up paths and API keys.
- **Environment Preparation**: Calls functions to create necessary directories and select statement types based on user input.
- **PDF Processing**: Counts PDFs before and after splitting them for analysis readiness, providing feedback on the process.
- **Data Analysis and Extraction**: Initialises the Document Analysis Client, processes each PDF, extracts data, and aggregates the results.
- **Output Generation**: Writes the aggregated transaction and summary data to an Excel file.

### `prep_env.py`

Responsible for environment preparation tasks including directories creation and configuration loading.

- **`create_folders()`**: Prompts the user for a statement set name, creating structured directories for file processing stages.
- **`move_analysed_file()`**: Moves processed files to a designated folder post-analysis.
- **`load_statement_config()`**: Loads statement processing configuration from a YAML file.
- **`select_statement_type()`**: Enables user selection of statement type for processing, as defiend in the YAML configuration file.
-**`set_model_id()`**: Sets the model id to designated model type.
-**`copy_files()`**: Copies the source folder PDF files to the destination folder.

### `pdf_processor.py`

Contains functions for PDF manipulation, including counting pages and splitting documents based on content patterns.

- **`find_document_starts()`**: Scans a PDF for document start patterns, returning their page numbers.
- **`split_pdf()`**: Splits a PDF into separate documents based on start patterns.
- **`process_all_pdfs()`**: Orchestrates the scanning and splitting of PDFs within a folder, handling single and multiple document PDFs.

### `doc_ai_utils.py`

Interfaces with the Azure Document Analysis Client for document analysis.

- **`initialise_analysis_client()`**: Sets up the Document Analysis Client with necessary credentials.
- **`analyse_document()`**: Analyses a document using the specified model, extracting structured data.

### `csv_utils.py`

Handles the extraction, transformation, and formatting of data from the analysis results.

- **`extract_static_info()`**: Extracts static information relevant across all documents of a certain type.
- **`process_transactions()`**: Processes dynamic transactional data from documents.
- **`extract_and_process_summary_info()`**: Extracts and formats summary information from document analysis results.
- **`write_transactions_and_summaries_to_excel()`**: Writes formatted transaction and summary data to an Excel file.

### `count_pdfs.py`

Provides utilities for counting PDFs and their pages before and after processing, aiding in validation processes.

- **`count_pdf_pages()`**: Counts the pages in a single PDF.
- **`process_pdf_count()`**: Aggregates file and page counts across a set of folders.
- **`save_to_excel()`**: Writes detailed and summary page count data to an Excel file.

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