import re
from datetime import datetime

def parse_dpkg_history(filename="history.log"):
    """Parses the dpkg history log file and extracts relevant information."""
    package_changes = []
    with open(filename, "r") as f:
        for line in f:
            match = re.match(r'^(.+)\s+(.*) installed\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.+?)\s+(.+)', line)
            if match:
                package, version, installed_date, removed_date = match.groups()
                installed_date = datetime.strptime(installed_date, '%Y-%m-%d %H:%M:%S')
                removed_date = datetime.strptime(removed_date, '%Y-%m-%d %H:%M:%S')
                package_changes.append({
                    "package": package,
                    "version": version,
                    "installed_date": installed_date,
                    "removed_date": removed_date,
                })
    return package_changes

# Example usage:
history = parse_dpkg_history('/var/log/apt/history.log')
for change in history:
    print(f"{change['package']}: {change['version']} ({change['installed_date']}) installed and removed on {change['removed_date']}") 