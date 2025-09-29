PROGRAM="pc-mobility-print-printer-setup-1.0.336[libraryprintq.printq.queensu.ca].exe"
LD_PRELOAD="$PWD/intercept.so" wine $PROGRAM
URL_FILE=$(ls -td /tmp/* | grep "captured-url" | head -n 1)
echo "Found $URL_FILE"
lpadmin -p LibraryPrintQ -E -v $(cat $URL_FILE)
if [ $? -eq 0 ]; then
    echo "Added Printer LibraryPrintQ"
else
    echo "Failed to add Printer"
fi
rm $URL_FILE

