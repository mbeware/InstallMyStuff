# InstallMyStuff

script that call the right package manager and log actions so they can be reproduced/documented.

## Folders :

### Protoypes :

Test programs and experimentation. those programs should Aonly read installations and sometimes create files in the current directory. If a program install or change an existing file, there will be a warning in the code, and at runtime.

### TestLogs/<package manager> :

Test logs for that package manager. sometime, there is a .result file that include the expected result (for human as sometimes it's the final package list, but most of the time, it is the intermediate list with all Install and Remove list, with date/time, versions and all)

### lib :

Common libraries shared amongst all tools

### doc :

I wish... A programmer can dream.

### src/ims

Sources for InstallMyStuff main core, including the command line interface.

### src/ims-tui (wish list item)

Sources for the text user interface (with menu and choice lists)

### src/ims-gui (wish list item)

Sources for the graphic user interface (tkinter or gtk... we will see)
