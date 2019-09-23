# Anemone Feeder
Anemone Feeder is a simulation of food particle drifting (random walk in three
dimensions) around and being selectively consumed by an anemone. The model and
simulation are configured using a file in the same directory as the script and
named 'config.ini'. See the included 'example-config.ini' for more.

## Usage
Build a virtual environment in the project directory, install the dependancies,
and run using python 3.5+

```
git clone git@github.com:tkegan/Anemone-Feeder.git
cd Anemone-Feeder
python -m venv .
source bin/activate
python -m pip install -r requirements.txt
```

Make sure you provide a 'config.ini'!

```
python anemone-feeder.py
```

## Author
Tom Egan <tkegan@greenneondesign.com>

## License
GNU Lesser General Public License (LGPL) v3
See also LICENSE

## To Do

- allow for outputting apointcloud file of all or select timesteps

- document configuration file

- modularize?