# yt_collection
Python script for collecting basic YouTube search results

## Requirements
Run with Python 3. Install required packages with
```commandline
pip install -r requirements.txt
```

## Configuration
Make a copy of the configuration file template
```commandline
cp conf_template.py conf.py
```
Add your YouTube API key and the name of the input file to the `conf.py` file.


## Input
The script reads from the file specified in `conf.py`. The file should contain on each line a query phrase and the
desired maximum number of days elapsed since the video release. Edit the `niches_template.txt` file as needed or make a
copy and change the file name in `conf.py'.


## Execution
```commandline
python3 main.py
```