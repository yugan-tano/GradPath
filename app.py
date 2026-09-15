# -*- coding: utf-8 -*-
import sys

# Keep all diagnostics in one stream so the Windows launcher can display and
# persist them without PowerShell converting stderr lines into error records.
sys.stderr = sys.stdout

from engine.server import main


if __name__ == "__main__":
    main()
