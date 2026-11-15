"""ACS allocation (imputation) tables for the source coverage check, every tract, 50 states + DC.
These count how many answers the Census Bureau filled in rather than took from a respondent.
Same fetch as 01_fetch_acs.py; saved under data/raw/acs/<year>/."""
import importlib.util, os
spec = importlib.util.spec_from_file_location("f", os.path.join(os.path.dirname(__file__), "01_fetch_acs.py"))
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
f.TABLES = {2024: ["B99192", "B99231", "B992701", "B99221", "B992518"], 2019: ["B99231"]}
if __name__ == "__main__":
    f.main()
