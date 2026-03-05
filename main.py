#!/usr/bin/env python3
"""
Camino - GPS-triggered audio guide app
Entry point for Buildozer/Android builds
"""

# Import and run the actual application
from app.main import CaminoApp

if __name__ == '__main__':
    CaminoApp().run()
