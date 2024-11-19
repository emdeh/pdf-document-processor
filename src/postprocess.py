import argparse
import os
from postprocess_utils import ExcelHandler, PDFPostProcessor
from utils import Logger

def main():
    # Dynamically generate the task list and descriptions for the help message
    excel_task_help = "\n".join([f"{task}: {details['description']}" for task, details in ExcelHandler.task_registry.items()])
    pdf_task_help = "\n".join([f"{task}: {details['description']}" for task, details in PDFPostProcessor.task_registry.items()])

    # Parse command-line arguments using RawTextHelpFormatter to preserve formatting
    parser = argparse.ArgumentParser(
        description=f'Postprocessing tasks.\n\n**AVAILABLE EXCEL TASKS:\n{excel_task_help}\n\n**AVAILABLE PDF TASKS:\n{pdf_task_help}',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '-i', '--input', 
        type=str, 
        required=True, 
        help='Path to the input file or folder (Excel or PDFs)'
        )
    
    parser.add_argument(
        '--tasks', 
        type=str, 
        nargs='+', 
        help='List of post-processing tasks to perform.'
        )
    
    args = parser.parse_args()

    input_path = args.input

    # Set up logger
    logger = Logger.get_logger("Postprocessor", log_to_file=True)
    logger.info("Starting postprocessing script...")

    # Determine if input is an Excel file or a directory containing PDFs
    if os.path.isfile(input_path) and input_path.lower().endswith('.xlsx'):
        # Excel processing
        output_file = f"{os.path.splitext(input_path)[0]}_processed{os.path.splitext(input_path)[1]}"
        excel_handler = ExcelHandler(input_path)

        if args.tasks:
            for task_name in args.tasks:
                if task_name in ExcelHandler.task_registry:
                    logger.info(
                        "Performing Excel task: %s",
                        task_name
                    )
                    task_func_name = ExcelHandler.task_registry[task_name]['func']
                    task_func = getattr(ExcelHandler, task_func_name)
                    excel_handler.transactions_df = task_func(excel_handler.transactions_df)
                else:
                    logger.info(
                        "Task '%s' not recognised for Excel. Skipping.",
                        task_name
                    )
                    
        else:
            logger.info("No Excel task specified. Exiting.")
            exit(1)

        excel_handler.save(output_file)
        logger.info(
            "Postprocessing complete. Output saved to: %s",
            output_file
        )

    elif os.path.isdir(input_path):
    # PDF processing
        subdirs = [os.path.join(input_path, d) for d in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, d))]
        if subdirs:
            # Iterate over each subdirectory
            for subdir in subdirs:
                logger.info(
                    "Processing PDFs in subdirectory: %s",
                    subdir
                )
                pdf_processor = PDFPostProcessor(subdir)

                if args.tasks:
                    for task_name in args.tasks:
                        if task_name in PDFPostProcessor.task_registry:
                            logger.info(
                                "Performing PDF task: %s on %s",
                                task_name,
                                subdir
                            )
                            task_func_name = PDFPostProcessor.task_registry[task_name]['func']
                            task_func = getattr(pdf_processor, task_func_name)
                            task_func()
                        else:
                            logger.info(
                                "Task '%s' not recognised for PDFs. Skipping.",
                                task_name
                            )
                else:
                    logger.info("No PDF tasks specified. Exiting.")
                    exit(1)

        # After processing subdirectories, check input base directory.
        pdf_processor = PDFPostProcessor(input_path)

        if args.tasks:
            for task_name in args.tasks:
                if task_name in PDFPostProcessor.task_registry:
                    logger.info(
                        "Performing PDF task:",
                        task_name
                    )
                    task_func_name = PDFPostProcessor.task_registry[task_name]['func']
                    task_func = getattr(pdf_processor, task_func_name)
                    task_func()
                else:
                    logger.info(
                        "Task '%s' not recognised for PDFs. Skipping",
                        task_name
                    )
        else:
            logger.info("No PDF tasks specified. Exiting.")
            exit(1)

        logger.info("PDF postprocessing complete.")

    else:
        logger.info("Invalid input path. Please provide a valid Excel file or directory containing PDFs.")
        exit(1)

if __name__ == '__main__':
    main()