# sts-train-collector

This is a plugin for the signal box simulation [Stellwerksim](https://www.stellwerksim.de). This plugin allows to collect and save all trains in a running signal box instance to CSV.

## Prerequisites 

1. Python >= 3.5 installed
2. A free user account for Stellwerksim

## Usage 

1. Connect to a Stellwerksim signal box instance (either demo or live)
2. Enable the plugin interface of the signal box instance (Optionen -> Pluginschnitstelle starten)
3. Start the plugin: `python app/sts-train-collector.py`

Afterwards the plugin will collect all currently present trains and their details and routes for the given instance and write them to `data/<instance name>.csv`. The result will be updated alll 10 minutes of runtime.
