import os
import shutil

def get_excluded_folders(src):
    """
    Prompts the user to exclude specific top-level folders by selecting their numbers.
    Returns a list of excluded folder names.
    """
    # Get only the top-level (parent) directories
    folders = [d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d))]

    if not folders:
        print("\nNo top-level subfolders found to exclude.")
        return []

    print("\nTop-level folders in the source directory:")
    for i, folder in enumerate(folders):
        print(f"  {i + 1}. {folder}")

    selected_numbers = input("\nEnter the numbers of the folders to exclude (comma-separated): ").strip()
    if not selected_numbers:
        return []

    try:
        selected_indices = [int(num.strip()) - 1 for num in selected_numbers.split(',')]
        excluded = [folders[i] for i in selected_indices if 0 <= i < len(folders)]
        return excluded
    except ValueError:
        print("Invalid input. No folders will be excluded.")
        return []

def copy_folder(src, dest, excluded_folders):
    """
    Copies files from the source folder to the destination folder excluding specified folders.
    """
    if not os.path.exists(dest):
        os.makedirs(dest)

    for root, dirs, files in os.walk(src):
        # Skip excluded top-level folders
        dirs[:] = [d for d in dirs if d not in excluded_folders]

        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest, os.path.relpath(src_file, src))
            
            # Create destination directories if they don't exist
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(src_file, dest_file)
            print(f"Copied: {src_file} to {dest_file}")

def save_file_contents(src, excluded_folders, output_file):
    """
    Reads and saves the content of all files (excluding specified folders) to a single text file.
    Displays the path of each file above its content.
    """
    with open(output_file, 'w') as output:
        for root, dirs, files in os.walk(src):
            # Skip excluded top-level folders
            dirs[:] = [d for d in dirs if d not in excluded_folders]

            for file in files:
                src_file = os.path.join(root, file)
                try:
                    with open(src_file, 'r') as f:
                        content = f.read()
                        output.write(f"\n{'='*80}\n")
                        output.write(f"File Path: {src_file}\n")
                        output.write(f"{'='*80}\n")
                        output.write(content + "\n")
                except Exception as e:
                    print(f"Could not read {src_file}: {e}")

# Main Script
src_folder = input("Enter the source folder path: ").strip()
excluded_folders = get_excluded_folders(src_folder)

print("\nChoose an output option:")
print("1. Copy files to a destination folder")
print("2. Save contents of files to a text file")
print("3. Both (Copy files and save contents to a text file)")

option = input("Enter your choice (1/2/3): ").strip()

if option == "1":
    dest_folder = input("Enter the destination folder path: ").strip()
    copy_folder(src_folder, dest_folder, excluded_folders)
    print("\nFiles have been copied successfully.")
elif option == "2":
    output_text_file = input("Enter the path for the output text file: ").strip()
    save_file_contents(src_folder, excluded_folders, output_text_file)
    print("\nContents have been saved successfully.")
elif option == "3":
    dest_folder = input("Enter the destination folder path: ").strip()
    output_text_file = input("Enter the path for the output text file: ").strip()
    copy_folder(src_folder, dest_folder, excluded_folders)
    save_file_contents(src_folder, excluded_folders, output_text_file)
    print("\nFiles have been copied and contents saved successfully.")
else:
    print("Invalid option. Please run the script again.")
