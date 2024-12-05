
if [ -d firefox ] ; then
    echo "Adding './firefox' into PATH"
    export PATH=$PWD/firefox:$PATH
    # export LD_LIBRARY_PATH=$PWD/firefox:$LD_LIBRARY_PATH
fi

if [ -d geckodriver-linux64-035 ] ; then
    echo "Adding './geckodriver-linux64-035' into PATH"
    export PATH=$PWD/geckodriver-linux64-035:$PATH
fi


# If working with Chrome/Chromeium
#export PATH=$PWD/chromedriver-linux64-116:$PATH

source ./python3-for-lrl/bin/activate

