import re

regex_extractDataAndBlock = r"(?<=Start-Date: )(\d{4}-\d{2}-\d{2}  \d{2}:\d{2}:\d{2})\n*((?:[\s\S]*?))(?=End-Date)"
regex_extractCommandLinePackages = r'^Commandline: apt-get.*?install\s+([a-zA-Z0-9-]+(?:(?:\s+[a-zA-Z0-9-]+)*))\n'
regex_extractInstallRemoveAndPackages =  r'^(?:Install|Update|Upgrade|Remove):\s+((?:[a-zA-Z0-9-]+:[a-zA-Z0-9-]+\s*\([^\)]+\)(?!,\s*automatic),?\s*)+))'
regex_extractPackageNameAndVersion = r"([\w\-.+]+):\w+\s+\((.*?)\)"

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
    regex_extractDataAndBlock,
    re.MULTILINE | re.DOTALL
)

tst = re.findall(regex_extractDataAndBlock, log_block, re.MULTILINE |  re.DOTALL)


# Extract date, action, and packages from each matching block
results = []
for match in pattern.finditer(log_block):
    date = match.group(1)
    block = match.group(2)



    # Extract package details from the block
    # Commandline info 
    commandline_packages = re.findall(regex_extractCommandLinePackages, block, re.MULTILINE | re.DOTALL)
    
    for package,info in commandline_packages:
        print(f"{package},{date},Install")
    
    # Install info 
    pattern_install = re.compile(
        regex_extractInstallRemoveAndPackages, 
        re.MULTILINE | re.DOTALL
    )

    for package_match in pattern_install.finditer(block):
        action = package_match.group(1)
        packages = package_match.group(2)
    
        
        if action in ['Install', 'Remove']:
            package_list = re.findall(regex_extractPackageNameAndVersion, packages)
        
        
            # Append each package with date and action to the results
            for package,info in package_list:
                if "automatic" in info:
                    continue
                results.append((date, action, package))
                print(f"{package},{date},{action}")

