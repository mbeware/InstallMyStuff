import re

def parse_apt_history_log(log_path):
    # Regular expression to match installed packages
    install_pattern = re.compile(r"^Install: (.*)")

    installed_packages = []

    # Open the log file
    with open(log_path, 'r') as file:
        for line in file:
            match = install_pattern.search(line)
            if match:
                # Get the package(s) installed in the current line
                packages = match.group(1)
                # Split packages by commas and strip extra whitespace
                installed_packages.extend([pkg.split()[0] for pkg in packages.split(', ')])

    return installed_packages

# Path to the history.log file
log_path = "/var/log/apt/history.log"

# Get the list of installed packages
installed_packages = parse_apt_history_log(log_path)

# Print the installed packages
print("Installed packages:")
for package in installed_packages:
    print(package)
