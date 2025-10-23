These scripts allow you to add printq printers on linux. 

It uses the same logic as the native windows exe. 

The python scripts are reverse engineered and send the same http requests to printq servers to get your printer URI. One script can be used through cli, and the other provides a GTK frontend.

The shell script requires having the windows exe (you should be able to get that from your school/organization), and runs it with wine, hooking onto unlink and unlinkat to get the URI that gets fetched by the exe. This is possible because the installer works by adding outputting the URI to a temp file, and then using that to add it. It then deletes the file so you can just hook onto the deletion to get the URI.

## Instructions 
### Requirements
- cups
- gtk3
### Python Requirements
- requests

### GUI/GTK
Run the script, then add your host and port (if you don't know the host, it should be in the brackets of the official printq installer that you should be able to get from your institution).
Then fetch printers, and select your printer.
Then enter your username and password and click add printer.
```
python3 printq-ui.py
```

### CLI
```
usage: printq-cli.py [-h] [--host HOST] [--printer PRINTER] [--port PORT] [--locale LOCALE] [--scheme-https] [--insecure]

A CLI tool for adding printq printers to CUPS on linux.

options:
  -h, --help         show this help message and exit
  --host HOST        host (i.e. libraryprintq.printq.queensu.ca)
  --printer PRINTER  Printer name (if omitted, checks selected server for printers)
  --port PORT        Port for the printer server (default: 9164)
  --locale LOCALE    Locale parameter
  --scheme-https     Add &scheme=https param
  --insecure         Ignore SSL certificate errors
```

## EXE Hook Old Instructions
### Requirements
- wine
- cups

### Running
```
git clone https://github.com/c-ola/linux-printq
./linux-printq.sh <path/to/exe>
```

## Build
```
gcc -shared -fPIC -o intercept.so intercept.c -ldl
```

The intercept program was made by ChatGPT lmao in like 1 proompt.

