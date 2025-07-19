import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox

# Add the 'app' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import tkinterdnd2 as tkdnd
from app.pdf_merger_app import PDFMergerApp
from app.constants import APP_NAME, APP_VERSION, LOGGER_NAME
from app.common_imports import pymupdf, RARFILE_AVAILABLE
from app.exceptions import PDFMergerError


def main():
    # Use a temporary logger for the very early startup phase
    # The main logger will be configured by the App class based on config.
    startup_logger = logging.getLogger(f"{LOGGER_NAME}_Startup")
    startup_logger.setLevel(logging.INFO)
    if not startup_logger.hasHandlers():
        ch = logging.StreamHandler(sys.stderr)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        startup_logger.addHandler(ch)
        startup_logger.propagate = False # Don't pass up


    startup_logger.info(f"Attempting to start {APP_NAME} v{APP_VERSION}")

    # Log versions of core libraries for debugging
    try:
        startup_logger.info(f"PyMuPDF version: {pymupdf.__version__}, MuPDF library version: {pymupdf.mupdf_version}")
    except Exception as e:
        startup_logger.warning(f"Could not retrieve PyMuPDF version details: {e}")
    try:
        from app.common_imports import PdfWriter
        import pypdf
        startup_logger.info(f"pypdf version: {pypdf.__version__}")
    except ImportError:
         startup_logger.warning("pypdf library not found.")
    except Exception as e:
        startup_logger.warning(f"Could not retrieve pypdf version details: {e}")
    if RARFILE_AVAILABLE: # Use the flag defined at the top of this file
        try:
            from app.common_imports import rarfile
            startup_logger.info(f"rarfile version: {rarfile.__version__}")
        except Exception as e:
            startup_logger.warning(f"Could not retrieve rarfile version details: {e}")
    else:
        startup_logger.info("rarfile library not available.")


    root_tk_instance = None
    try:
        # Attempt to create the main Tkinter window with Drag and Drop support
        # tkdnd.TkinterDnD.enabledebug() # Uncomment for DND debugging
        root_tk_instance = tkdnd.TkinterDnD.Tk()
        startup_logger.info("TkinterDnD.Tk() instance created successfully.")
    except tk.TclError as e:
        startup_logger.critical(f"FATAL ERROR: Failed to initialize Tkinter/TkinterDnD: {e}", exc_info=True)
        try:
            # Fallback to basic Tk to show a graphical error message before exiting
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror(
                "Initialization Error",
                f"Failed to initialize the application's graphical interface.\n"
                f"This might be due to Tkinter or the Drag & Drop extension.\n\n"
                f"Error: {e}\n\n"
                "The application will now exit."
            )
        except Exception:
             print("Failed to show error message box. Please check logs.", file=sys.stderr)
        sys.exit(1)

    except Exception as e_general:
        startup_logger.critical(f"A critical unexpected error occurred during initialization: {e_general}", exc_info=True)
        try:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror(
                "Critical Initialization Error",
                f"An unexpected error occurred while starting the application: {e_general}\n\n"
                "Please check the logs for more details.\nThe application will now exit."
            )
        except Exception:
             print("Failed to show error message box. Please check logs.", file=sys.stderr)
        sys.exit(1)

    # If initialization was successful, create the main application instance.
    # This is where the main logger will be configured.
    try:
        app = PDFMergerApp(root_tk_instance)

        # Get the main application logger instance after it's configured
        main_app_logger = logging.getLogger(LOGGER_NAME)
        main_app_logger.info("Application instance created. Starting main event loop.")

        # Start the Tkinter event loop
        root_tk_instance.mainloop()

    except KeyboardInterrupt:
        logging.getLogger(LOGGER_NAME).info("Application terminated by user (KeyboardInterrupt).")

    except PDFMergerError as e:
        main_app_logger = logging.getLogger(LOGGER_NAME)
        main_app_logger.critical(f"A critical application error occurred: {e}", exc_info=True)
        if root_tk_instance and root_tk_instance.winfo_exists():
            messagebox.showerror(
                "Application Error",
                f"A critical error occurred: {e}\n\nPlease check logs for details.",
                parent=root_tk_instance
            )
        else:
            print(f"Critical application error: {e}", file=sys.stderr)

    except Exception as e_mainloop:
        main_app_logger = logging.getLogger(LOGGER_NAME)
        main_app_logger.critical(f"An unhandled exception occurred in the main event loop: {e_mainloop}", exc_info=True)
        if root_tk_instance and root_tk_instance.winfo_exists():
            messagebox.showerror(
                "Runtime Error",
                f"A critical error occurred: {e_mainloop}\n\nPlease check logs for details.",
                parent=root_tk_instance
            )
        else:
             print(f"Critical runtime error: {e_mainloop}", file=sys.stderr)

    finally:
        final_logger = logging.getLogger(LOGGER_NAME)
        final_logger.info(f"Exiting {APP_NAME} main process.")

if __name__ == "__main__":
    main()