import pandas as pd

class ExcelHandler:
    """
    A class to handle reading and writing of Excel files.
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.summary_df = None
        self.transactions_df = None
        self._load_excel_file()

    def _load_excel_file(self):
        """Loads the Excel file into DataFrames."""
        print(f"Loading Excel file: {self.file_path}")
        excel_file = pd.ExcelFile(self.file_path)
        self.summary_df = pd.read_excel(excel_file, sheet_name='summary')
        self.transactions_df = pd.read_excel(excel_file, sheet_name='transactions')

    def save(self, output_file):
        """Saves the DataFrames back to an Excel file."""
        print(f"Saving to: {output_file}")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            self.summary_df.to_excel(writer, sheet_name='summary', index=False)
            self.transactions_df.to_excel(writer, sheet_name='transactions', index=False)

def fill_missing_dates(transactions_df, **kwargs):
    """
    Fills missing dates in the 'Date' column by propagating the last known date downward.

    Args:
        transactions_df (pd.DataFrame): DataFrame containing transaction data.

    Returns:
        pd.DataFrame: Updated DataFrame with missing dates filled.
    """
    print("Filling missing dates in the 'Date' column...")
    transactions_df['Date'] = transactions_df['Date'].ffill()
    return transactions_df

# Additional post-processing tasks can be defined similarly
