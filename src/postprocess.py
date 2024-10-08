import argparse
import os
from postprocess_utils import ExcelHandler

def main():
    # Dynamically generate the task list and descriptions for the help message
    task_help = "\n".join([f"{task}: {details['description']}" for task, details in ExcelHandler.task_registry.items()])

    # Parse command-line arguments using RawTextHelpFormatter to preserve formatting
    parser = argparse.ArgumentParser(
        description=f'Postprocessing Script for Transaction Data.\n\nAvailable tasks:\n{task_help}',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-i', '--input', 
        type=str, 
        required=True, 
        help='Path to the input Excel file'
        )
    parser.add_argument(
        '--tasks', 
        type=str, 
        nargs='+', 
        help='List of postprocessing tasks to perform.'
        )
    args = parser.parse_args()

    input_dir = args.input
    output_file = (lambda fn: f"{os.path.splitext(fn)[0]}_processed{os.path.splitext(fn)[1]}")(input_dir)

    # If output_file is not provided, create a new file path in the same directory
    '''if args.output_file:
        output_file = args.input_dir
    else:
        file_name, file_extension = os.path.splitext(input_dir)
        output_file = f"{file_name}_processed{file_extension}"

    # Verify input file exists
    if not os.path.exists(input_dir):
        print(f"Input file does not exist: {input_dir}")
        exit(1)'''

    # Load the Excel file
    excel_handler = ExcelHandler(input_dir)

    # Perform selected tasks on the 'transactions' sheet
    if args.tasks:
        for task_name in args.tasks:
            if task_name in ExcelHandler.task_registry:
                print(f"Performing task: {task_name}")
                task_func_name = ExcelHandler.task_registry[task_name]['func']
                task_func = getattr(ExcelHandler, task_func_name)  # Use ExcelHandler here because it's a static method
                excel_handler.transactions_df = task_func(excel_handler.transactions_df)
            else:
                print(f"Task '{task_name}' not recognized. Skipping.")
    else:
        print("No tasks specified. Exiting.")
        exit(1)

    # Save the processed data to the output file
    excel_handler.save(output_file)

    print(f"Postprocessing complete. Output saved to: {output_file}")

if __name__ == '__main__':
    main()
