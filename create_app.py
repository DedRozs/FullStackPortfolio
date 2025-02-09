import os
import sys

def create_app(app_name, parent_folder="apps"):
    """Creates a Django app inside a parent folder, ensuring the directory exists."""
    
    # Ensure the parent directory exists
    parent_path = os.path.join(os.getcwd(), parent_folder)
    os.makedirs(parent_path, exist_ok=True)  # Creates the folder if it doesn’t exist
    
    # Full app path
    app_path = os.path.join(parent_path, app_name)
    
    # Ensure the parent directory exists
    app_path = os.path.join(os.getcwd(), f"{parent_path}/{app_name}")
    os.makedirs(f"{parent_path}/{app_name}", exist_ok=True)  # Creates the folder if it doesn’t exist

    # Run the Django command to create the app
    os.system(f"python manage.py startapp {app_name} {app_path}")

    print(f"✅ Django app '{app_name}' created inside '{parent_folder}/'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Please provide an app name.\nUsage: python create_app.py <app_name>")
        sys.exit(1)

    app_name = sys.argv[1]
    create_app(app_name)