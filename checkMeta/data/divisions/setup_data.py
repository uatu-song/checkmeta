from data.loaders import ensure_data_directories, update_data_directories, get_data_filepath

def setup_data_directories():
    """Create the data directory structure"""
    print("Setting up data directories...")
    ensure_data_directories()
    update_data_directories()
    print("Data directories created.")