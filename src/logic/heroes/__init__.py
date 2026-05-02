import os
import importlib

# 📂 The Automatic Roll-Call:
# This runs the moment 'import src.logic.heroes' is called.
curr_dir = os.path.dirname(__file__)

for file in os.listdir(curr_dir):
    if file.endswith(".py") and file != "__init__.py":
        # Construct the module path (e.g., src.logic.heroes.black_cat)
        module_name = f"src.logic.heroes.{file[:-3]}"
        
        # ⚡ IMPORTING the module triggers the @SpecialAbilitySystem.register decorator
        importlib.import_module(module_name)
        