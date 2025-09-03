#!/usr/bin/env python3
"""
IMS - Install my stuff
A command-line tool to track package installations and removals across different package managers.
"""

import json
import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import platformdirs


class Config:
    """Handle application configuration"""
    def __init__(self):
        self.appname = "ims"
        self.orgname = "mbeware"
        self.default_config_dir = str(platformdirs.user_config_path(self.appname,self.orgname) )
        self.config_file = f"{self.default_config_dir}/ims_config.json"
        self.default_config = {
            "data_folder": str(platformdirs.user_data_path(self.appname,self.orgname) ),
            "default_package_manager": "apt",
            "package_managers": {
                "apt": {"install" : ["sudo", "apt", "install", "-y"],
                        "uninstall": ["sudo", "apt", "remove", "-y"]},
                "flatpak":{"install" : ["flatpak", "install", "-y"],
                           "uninstall" : ["flatpak", "uninstall", "-y"]},
                "pip": {"install" :["pip", "install"],
                        "uninstall" : ["pip", "uninstall", "-y"]}
            }
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception:
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
   
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        os.makedirs(self.default_config_dir, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def edit_config(self):
        """Open config file in default editor"""
        if sys.platform == "win32":
            os.startfile(self.config_file)
        else:
            subprocess.call(["xdg-open", self.config_file])


class IMSData:
    def __init__(self, config: Config):
        self.config = config
        self.data_folder = Path(config.config["data_folder"]).expanduser()
        self.data_folder.mkdir(parents=True, exist_ok=True)
        
        self.uncommitted_file = self.data_folder / "uncommitted.json"
        self.committed_file = self.data_folder / "committed.json"
        
        self.uncommitted = self.load_json_file(self.uncommitted_file)
        self.committed = self.load_json_file(self.committed_file)
    
    def load_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {file_path}, starting with empty list")
        return []
    
    def save_json_file(self, file_path: Path, data: List[Dict[str, Any]]):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_uncommitted(self):
        self.save_json_file(self.uncommitted_file, self.uncommitted)
    
    def save_committed(self):
        self.save_json_file(self.committed_file, self.committed)

class IMS:
    def __init__(self):
        self.config = Config()
        self.data = IMSData(self.config)
    
    def get_package_manager_command(self, package_spec: str, cmd_id: str) -> tuple[list, str, str]:
        """Parse package specification and return (package_manager, package_name)"""
        if ':' in package_spec:
            pm_id, package_name = package_spec.split(':', 1)
        else:
            pm_id = self.config.config["default_package_manager"]
            package_name = package_spec

        if pm_id in self.config.config["package_managers"]:
            if cmd_id in self.config.config["package_managers"][pm_id]:
                return self.config.config["package_managers"][pm_id][cmd_id], pm_id, package_name
            else:
                print(f"Unknown command id {cmd_id} for package manager ID: {pm_id}")
                sys.exit(1)
        else:
            print(f"Unknown package manager ID: {pm_id}")
            sys.exit(1)

    
    def install_package(self, package_spec: str, commit_immediately: bool = False):
        """Install a package and log it"""
        pm_command, pm_name, package_name = self.get_package_manager_command(package_spec, "install")
        cmd = pm_command + [package_name]
        
        print(f"Installing {package_name} with {pm_name} - {' '.join(cmd)}...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.returncode == 0 :
                print(f"Successfully installed {package_name}")
            
                # Log the installation
                entry = {
                    "action": "install",
                    "package_name": package_name,
                    "package_manager_name": pm_name,
                    "package_manager_command": cmd,
                    "date": datetime.now().isoformat(),
                    "state": "committed" if commit_immediately else "uncommitted"
                }
                
                if commit_immediately:
                    self.data.committed.append(entry)
                    self.data.save_committed()
                else:
                    self.data.uncommitted.append(entry)
                    self.data.save_uncommitted()
            else:
                print(f"Failed to install {package_name} - error code {result.returncode}: ")
                if result.stdout :
                    print(f"std_out : {result.stdout}")
                if result.stderr :
                    print(f"std_err : {result.stderr}")

                
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")
            if e.stdout:
                print(f"stdout:\n {e.stdout}")
            if e.stderr:
                print(f"Error:\n {e.stderr}")
    
    def commit_packages(self):
        """Move all uncommitted packages to committed list"""
        if not self.data.uncommitted:
            print("No uncommitted packages to commit")
            return
        
        commit_entry = {
            "action": "commit",
            "date": datetime.now().isoformat(),
            "packages_count": len(self.data.uncommitted)
        }
        
        # Update state of uncommitted packages and move to committed
        for entry in self.data.uncommitted:
            entry["state"] = "committed"
            self.data.committed.append(entry)
        
        # Add commit entry
        self.data.committed.append(commit_entry)
        
        # Clear uncommitted list
        self.data.uncommitted = []
        
        self.data.save_committed()
        self.data.save_uncommitted()
        
        print(f"Committed {commit_entry['packages_count']} packages")
    
    def remove_package(self, package_spec: str):
        """Remove a package and update logs"""
        pm_command,pm_name, package_name = self.get_package_manager_command(package_spec,"uninstall")
        cmd = pm_command + [package_name]
               
       
        print(f"Uninstalling {package_name} with {pm_name} - {' '.join(cmd)}...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.returncode == 0 :
                print(f"Successfully removed {package_name}")

                # Check if package is in uncommitted list
                for i, entry in enumerate(self.data.uncommitted):
                    if entry["package_name"] == package_name and entry["package_manager_name"] == pm_name:
                        if entry["action"] == "install":
                            # Remove from uncommitted list
                            self.data.uncommitted.pop(i)
                            self.data.save_uncommitted()
                            print(f"Removed {package_name} from uncommitted list")

                # Add removal entry to committed list
                entry = {
                    "action": "remove",
                    "package_name": package_name,                    
                    "package_manager_name": pm_name,
                    "package_manager_command": cmd,
                    "date": datetime.now().isoformat(),
                    "state": "committed"
                }
            
                self.data.committed.append(entry)
                self.data.save_committed()
            else:
                print(f"Failed to remove {package_name} - error code {result.returncode}: ")
                if result.stdout :
                    print(f"std_out : {result.stdout}")
                if result.stderr :
                    print(f"std_err : {result.stderr}")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to remove {package_name}: {e}")
            if e.stderr:
                print(f"Error: {e.stderr}")
    
    def get_packages_at_tag(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of installed packages at a specific tag or current state"""
        installed_packages = {}
        
        # Process committed entries up to tag
        for entry in self.data.committed:
            if tag and entry.get("action") == "tag" and entry.get("tag_name") == tag:
                break
            
            if entry["action"] == "install":
                key = f"{entry['package_manager_name']}:{entry['package_name']}"
                installed_packages[key] = entry
            elif entry["action"] == "remove":
                key = f"{entry['package_manager_name']}:{entry['package_name']}"
                installed_packages.pop(key, None)
        
        # If no tag specified, include uncommitted packages
        if not tag:
            for entry in self.data.uncommitted:
                if entry["action"] == "install":
                    key = f"{entry['package_manager_name']}:{entry['package_name']}"
                    installed_packages[key] = entry
        
        return list(installed_packages.values())
    
    def list_installed(self, tag: Optional[str] = None):
        """List all installed packages at a tag or current state"""
        packages = self.get_packages_at_tag(tag)
        
        if not packages:
            print("No packages installed")
            return
        
        print(f"Installed packages{'at tag ' + tag if tag else ' (current state)'}:")
        print(f"{'Package':<30} {'Manager':<15} {'State':<12} {'Install Date':<20}")
        print("-" * 80)
        
        for pkg in sorted(packages, key=lambda x: x['date']):
            print(f"{pkg['package_name']:<30} {pkg['package_manager_name']:<15} "
                  f"{pkg['state']:<12} {pkg['date'][:19]:<20}")
    
    def list_all(self):
        """List all entries (installed, removed, commits, tags)"""
        print("All entries:")
        print(f"{'Action':<12} {'Package':<25} {'Manager':<12} {'State':<12} {'Date':<20}")
        print("-" * 85)
         
        # Show committed entries
        for entry in self.data.committed:
            if entry["action"] in ["install", "remove"]:
                print(f"{entry['action']:<12} {entry['package_name']:<25} "
                      f"{entry['package_manager_name']:<12} {entry['state']:<12} {entry['date'][:19]:<20}")
            elif entry["action"] == "commit":
                print(f"{'COMMIT':<12} {str(entry['packages_count'])+' packages':<26}"
                      f"{'N/A':<12} {'N/A':<12} {entry['date'][:19]:<20}")
            elif entry["action"] == "tag":
                print(f"{'TAG':<12} {entry['tag_name']:<25} "
                      f"{'N/A':<12} {'N/A':<12} {entry['date'][:19]:<20}")
        
        # Show uncommitted entries
        for entry in self.data.uncommitted:
            print(f"{entry['action']:<12} {entry['package_name']:<25} "
                  f"{entry['package_manager_name']:<12} {entry['state']:<12} {entry['date'][:19]:<20}")
    
    def generate_install_script(self, tag: Optional[str] = None):
        """Generate a script to reinstall packages at a tag or current state"""
        packages = self.get_packages_at_tag(tag)
        
        if not packages:
            print("No packages to generate script for")
            return
        
        script_name = f"reinstall_{'tag_' + tag if tag else 'current'}.sh"
        
        with open(script_name, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Generated by IMS - Install My Stuff\n")
            f.write(f"# Reinstall script for {'tag: ' + tag if tag else 'current state'}\n")
            f.write(f"# Generated on: {datetime.now().isoformat()}\n\n")
            
            
            for pkg in packages:
                if pkg['state'] == 'committed':  # Only include committed packages
                    f.write(f"{' '.join(pkg['package_manager_command'])} \n")
            f.write("\n")

        os.chmod(script_name, 0o755)
        print(f"Generated install script: {script_name}")
    
    def add_tag(self, tag_name: str):
        """Add a tag to the committed list"""
        entry = {
            "action": "tag",
            "tag_name": tag_name,
            "date": datetime.now().isoformat()
        }

        for i, entry in enumerate(self.data.committed):
            if entry.get("action") == "tag" and entry.get("tag_name") == tag_name:
                print(f"Tag '{tag_name}' already exists")
                return 

        self.data.committed.append(entry)
        self.data.save_committed()
        print(f"Added tag: {tag_name}")
    
    def remove_tag(self, tag_name: str):
        """Remove a tag from the committed list"""
        for i, entry in enumerate(self.data.committed):
            if entry.get("action") == "tag" and entry.get("tag_name") == tag_name:
                self.data.committed.pop(i)
                self.data.save_committed()
                print(f"Removed tag: {tag_name}")
                return
        
        print(f"Tag '{tag_name}' not found")

def main():
    parser = argparse.ArgumentParser(description="IMS - Install My Stuff")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install a package')
    install_parser.add_argument('package', help='Package specification (manager:package or package)')
    
    # Install commit command
    install_commit_parser = subparsers.add_parser('install_commit', help='Install and commit immediately')
    install_commit_parser.add_argument('package', help='Package specification')
    
    # Commit command
    subparsers.add_parser('commit', help='Commit all uncommitted packages')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a package')
    remove_parser.add_argument('package', help='Package specification')
    
    # List installed command
    list_installed_parser = subparsers.add_parser('list_installed', help='List installed packages')
    list_installed_parser.add_argument('tag', nargs='?', help='Tag to list packages for')
    
    # List all command
    subparsers.add_parser('list_all', help='List all entries')
    
    # Generate install script command
    geninstall_parser = subparsers.add_parser('geninstall', help='Generate install script')
    geninstall_parser.add_argument('tag', nargs='?', help='Tag to generate script for')
    
    # Add tag command
    add_tag_parser = subparsers.add_parser('add_tag', help='Add a tag')
    add_tag_parser.add_argument('tag_name', help='Tag name')
    
    # Remove tag command
    remove_tag_parser = subparsers.add_parser('remove_tag', help='Remove a tag')
    remove_tag_parser.add_argument('tag_name', help='Tag name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    ims = IMS()
    
    try:
        if args.command == 'install':
            ims.install_package(args.package)
        elif args.command == 'install_commit':
            ims.install_package(args.package, commit_immediately=True)
        elif args.command == 'commit':
            ims.commit_packages()
        elif args.command == 'remove':
            ims.remove_package(args.package)
        elif args.command == 'list_installed':
            ims.list_installed(args.tag)
        elif args.command == 'list_all':
            ims.list_all()
        elif args.command == 'geninstall':
            ims.generate_install_script(args.tag)
        elif args.command == 'add_tag':
            ims.add_tag(args.tag_name)
        elif args.command == 'remove_tag':
            ims.remove_tag(args.tag_name)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()