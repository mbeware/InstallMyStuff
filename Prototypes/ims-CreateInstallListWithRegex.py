import re

installed_packages = []

# Path to the history.log file
log_path = "/var/log/apt/history.log" # official log location
log_path = "/home/mbeware/Documents/dev/InstallMyStuff/TestLogs/apt/history.log" # test log

with open(log_path, 'r') as file:
    log_block = file.read()


####
#  The date is wrong, because some block don't have "Install" or "Remove". We need to accept all blocks 
#  and we will filter later for Install and Remove

# Updated regex pattern to capture each block with Start-Date, Install/Remove, and package details
pattern = re.compile(
    r'Start-Date:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\n.*?\n(Install|Update|Upgrade|Remove):\s+([^E]+?)\nEnd-Date:',
    re.MULTILINE | re.DOTALL
)

# Extract date, action, and packages from each matching block
results = []
for match in pattern.finditer(log_block):
    date = match.group(1)
    action = match.group(2)
    packages = match.group(3)
    
    if action in ['Install', 'Remove']:
        # Find individual package names without "automatic" in parentheses
        # package_list = re.findall(r'([\w\-.+]+):\w+\s+\((?!.*automatic).*?\)', packages)
        package_list = re.findall(r"([\w\-.+]+):\w+\s+\((.*?)\)", packages)
        
        
        # Append each package with date and action to the results
        for package,info in package_list:
            if "automatic" in info:
                continue
            results.append((date, action, package))
            print(f"{package},{date},{action}")

