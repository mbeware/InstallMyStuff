import sys

def extract_packages(log_file):
    interesting_packages = set()

    with open(log_file, 'r') as f:
        block_started = False
        block = ""

        for line in f:
            line = line.strip()
            if line.startswith("Start-Date:"):
                block_started = True
                block = ""
            elif line.startswith("End-Date:"):
                block_started = False
                if "Requested-By:" in block and "Install:" in block:
                    requested_by_index = block.index("Requested-By:")
                    install_index = block.index("Install:")
                    requested_by_entry = block[requested_by_index:install_index]
                    install_entry = block[install_index:]

                    install_lines = install_entry.split(')')
                    for install_line in install_lines:
                        if "automatic" not in install_line:
                            package = install_line.split(":")[0].strip()
                            interesting_packages.add(package)

            if block_started:
                block += line

    return interesting_packages


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]
    packages = extract_packages(log_file)

    for package in packages:
        print(package)

