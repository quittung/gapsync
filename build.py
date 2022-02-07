import os
import zipapp

if not os.path.exists("dist"):
    os.mkdir("dist")
    
zipapp.create_archive("gapsync", "dist/gapsync", "/usr/bin/python3", compressed=True)