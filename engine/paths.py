
import os

def get_project_root():
    """Works on Colab (/content/stock_alert_engine) and GitHub Actions."""
    colab_path  = "/content/stock_alert_engine"
    github_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if os.path.exists(colab_path):
        return colab_path
    return github_path

def get_config_path():
    return os.path.join(get_project_root(), "config", "config.yaml")

def get_alerts_path():
    return os.path.join(get_project_root(), "config", "alerts.json")

def get_history_path_from_cfg():
    import yaml
    with open(get_config_path()) as f:
        cfg = yaml.safe_load(f)
    return os.path.join(get_project_root(), cfg["storage"]["history_file"])

def get_archive_folder_from_cfg():
    import yaml
    with open(get_config_path()) as f:
        cfg = yaml.safe_load(f)
    return os.path.join(get_project_root(), cfg["storage"]["archive_folder"])
