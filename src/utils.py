# src/utils.py
import logging

def ask_user_to_continue():
    """
    Asks the user if they want to continue or stop.

    Returns:
        None
    """
    user_input = input("Would you like to continue to the next stage? (y/n): ")

    while True:
        if user_input.lower() == "n":
            print("Stopping the program.")
            quit()
        elif user_input.lower() == "y":
            print("Continuing to the next stage.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            user_input = input("Would you like to continue to the processing stage? (y/n): ")

class Logger:
    @staticmethod
    def get_logger(name, level=logging.DEBUG, log_to_file=False, log_file='app.log'):
        """
        Returns a logger instance for the specified name.
        
        :param name: Name for the logger (typically the class name)
        :param level: Logging level (default: DEBUG)
        :param log_to_file: If True, log messages will also be saved to a file (default: False)
        :param log_file: File to log messages if log_to_file is True (default: 'app.log')
        :return: Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not logger.hasHandlers():
            # Create console handler
            ch = logging.StreamHandler()
            ch.setLevel(level)

            # Create a formatter with time, name, level, and message
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            # Optional: log to file if log_to_file is True
            if log_to_file:
                fh = logging.FileHandler(log_file)
                fh.setLevel(level)
                fh.setFormatter(formatter)
                logger.addHandler(fh)

        return logger
