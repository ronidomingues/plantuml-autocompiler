import os
import glob
import shutil
import platform
import subprocess
import logging
from tkinter import Tk, filedialog

# Setting Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Setting Constants
PLANTUML_URL = "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"

class UMLProcessor:
    def __init__(self):
        self.directory: str = ""
        self.files: list[str,...] = []
    def __is_linux(self) -> bool:
        return platform.system() == "Linux"
    def __get_files(self) -> bool:
        try:
            Tk().withdraw()
            self.directory = filedialog.askdirectory(title="Select a directory")
            if not self.directory:
                logging.warning("No directory selected")
                return False
            self.files = [
                os.path.join(self.directory, file)
                for file in sorted(os.listdir(self.directory))
                if os.path.isfile(os.path.join(self.directory, file)) and not file.endswith('.py')
                ]
            if not self.files:
                logging.warning("No valid files were found in the directory")
                return False
            logging.info(f"{len(self.files)} files found in {self.directory}")
            return True
        except Exception as error:
            logging.error(f"Error selecting files: {error}")
            return False
    def __convert_png_to_pdf(self)-> None:
        if not self.__is_linux():
            logging.error("This module is only compatible with linux")
            return
        for file in self.files:
            if file.endswith(".png"):
                output_file = file.replace(".png", ".pdf")
                try:
                    subprocess.run(["convert", file, output_file], check=True)
                    logging.info(f"Converted: {file} -> {output_file}")
                except subprocess.CalledProcessError as error:
                    logging.error(f"Error coverting {file}: {error}")
        # Cleaning the folder:
        self.__cleanup(compress = ["puml"], delete = ["png"])
    def __cleanup(self, compress: list[str, ...] | None = None, delete: list[str, ...] | None = None) -> None:
        compress = compress or []
        delete = delete or []
        if not self.__is_linux():
            logging.error("This module is only compatible with linux")
            return
        if compress and not shutil.which("zip"):
            logging.error("Zip utility is not installed")
            return
        # Compress:
        for ext in compress:
            files_to_compress = glob.glob(os.path.join(self.directory, f"*.{ext}"))
            if not files_to_compress:
                logging.warning(f"No files .{ext} found to compact.")
                continue
            zip_path = os.path.join(self.directory, f"diagram_{ext}.zip")
            try:
                subprocess.run(["zip", "-j", zip_path] + files_to_compress, check=True)
                logging.info(f"Files .{ext} compressed into {zip_path}")
                # Delete after compaction:
                for file in files_to_compress:
                    os.remove(file)
                    logging.info(f"Removed: {file}")
            except subprocess.CalledProcessError as error:
                logging.error(f"Erro ao compactar arquivos .{ext}: {error}")
        # Direct Deletion:
        for ext in delete:
            files_to_delete = glob.glob(os.path.join(self.directory, f"*.{ext}"))
            if not files_to_delete:
                logging.warning(f"No files .{ext} found to delete.")
                continue
            confirm = input(f"Você realmente deseja excluir todos os arquivos .{ext}? (y/n): ").strip().lower()
            if confirm != "y":
                logging.info(f"Exclusão de arquivos .{ext} cancelada.")
                continue
            for file in files_to_delete:
                try:
                    os.remove(file)
                    logging.info(f"Removido: {file}")
                except OSError as error:
                    logging.error(f"Erro ao remover {file}: {error}")
    def __download_plantuml_jar(self, path: str) -> bool:
        try:
            subprocess.run([
                "wget", PLANTUML_URL, "-O", path
                ], check=True)
            logging.info("plantuml.jar downloaded successfully")
        except subprocess.CalledProcessError as error:
            logging.error(f"Error downloading plantuml.jar: {error}")
            return False
    def compile_uml_to_png(self, convert_to_pdf: bool = False) -> None:
        if not self.__is_linux():
            print("This module is only compatible with linux")
            return
        if not shutil.which("java"):
            logging.error("Java is not installed")
            return
        if not self.__get_files():
            return
        jar_path = "third-party/plantuml/"
        if "third-party" not in os.listdir("./"):
            subprocess.run(["mkdir", "-p", jar_path], check=True)
        jar_path = os.path.join(jar_path, "plantuml.jar")
        if not os.path.exists(jar_path):
            logging.warning("plantuml.jar not found. Downloading...")
            if not self.__download_plantuml_jar(jar_path):
                return
        for file in self.files:
            if file.endswith(".puml"):
                try:
                    subprocess.run(["java", "-jar", jar_path, "-tpng", file], check=True)
                    logging.info(f"Compiled: {file}")
                except subprocess.CalledProcessError as error:
                    logging.error(f"Compile error: {error}")
        if convert_to_pdf:
            self.__convert_png_to_pdf()
def main():
    processor = UMLProcessor()
    user_choice = input("Do you want to convert to PDF after compiling the .puml files? (y/n):").strip().lower()
    convert_to_pdf = user_choice == 'y'
    processor.compile_uml_to_png(convert_to_pdf = convert_to_pdf)

if __name__ == "__main__":
    main()
