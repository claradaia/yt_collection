# yt_collection
Python script for collecting basic YouTube search results.
This script uses the YouTube API to gather information from videos based on specified queries and release date
constraints, collected into .csv, .html and .pdf files. It also uses ChatGPT to generate a few recommendations of video 
titles for the specified queries.


## Installation
This is Python3 code. I used Python 3.11.


### Requirements
Install required packages with
```commandline
pip install -r requirements.txt
```

#### Windows
Python 3 is available on the Microsoft Store.

The WeasyPrint package that generates the PDF reports requires the Pango library. The recommended way to do this is to [install MSYS2](https://www.msys2.org/#installation) and run

```commandline
pacman -Smingw-w64-x86_64-pango
```

In the MSYS2 shell, then close the shell. More details on [the WeasyPrint documentation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).


#### Troubleshooting
If you encounter issues with missing modules, it may be because Windows is not looking for them in the right directory.
Check the path of `pip` and `python` with
```commandline
get-command pip
get-command python
```
If they do not match or do not look correct (for me that's `C:\Users\<myusername>\AppData\Local\Microsoft\WindowsApps\...`), check the system environment variables on Windows System Properties.


## Configuration
Make a copy of the configuration file template
```commandline
cp conf_template.py conf.py
```
You *must* add your API keys for YouTube and OpenAI to the `conf.py` file.
You can use the name of the input and logo files provided or change accordingly.


## Input
The script reads from the `QUERIES_FILE` specified in `conf.py`. The file should contain on each line a *query phrase*; the
desired maximum *number of days* elapsed since the video release; and the maximum number of *subscribers* of the video channels. Separate them with `;`.

Edit the `queries_template.txt` file as needed or make a
copy and change the file name in `conf.py`.

For the .html and .pdf files, the script uses the logo file stored in `static/images`. Set it in `conf.py` accordingly.


## Output
The script generates `collected_result_<date>.{csv,html,pdf}` files into the `output` directory.


## Execution
```commandline
python3 main.py
```