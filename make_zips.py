import zipfile
import os


def zip_dir(dir_name: str, files_to_add: list):
    zip_file_name = os.path.join(dir_name, f"{dir_name}.zip")
    zip_file = zipfile.ZipFile(zip_file_name, mode='w')

    try:
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                if file in files_to_add:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path)
    finally:
        zip_file.close()


if __name__ == '__main__':

    zip_dir("AnyPercentHelper", ['__init__.py', 'README.md'])
