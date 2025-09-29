This script is meant to allow for easy setup of printq printers on linux. It uses the native windows application, and runs it under wine, intercepting the printer URI that it creates, and then adding it cups.

## Instructions 
### Requirements
- wine
- cups

### Running
```
git clone https://github.com/c-ola/linux-printq
./linux-printq.sh
```

## Build
```
gcc -shared -fPIC -o intercept.so intercept.c -ldl
```

The intercept program was made by ChatGPT lmao in like 1 proompt.

