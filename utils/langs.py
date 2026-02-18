import os
import json
from pathlib import Path


class LangsSignleton:
    _instance = None

    def __new__(cls, lang):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

        return cls._instance


    def __init__(self, lang: str):


        if hasattr(self, "_initialized") and self._initialized:

            self.lang = lang

            return 
        

        self.initialized = True
        self.path = os.path.join(Path(__file__).resolve().parent.parent, "langs")
        print(self.path)
        self.lang = lang

        self.data_lang = {}

        for fname in os.listdir(self.path):

            if not fname.endswith(".json"):
                continue

            code = fname[:-5]

            full = os.path.join(self.path, fname)

            with open(full, 'r', encoding="utf-8") as f:
                self.data_lang[code] = json.load(f)


    def lang_msg(self, msg: str) -> str:
        lang_dict: dict = self.data_lang.get(self.lang, {})

        return lang_dict.get(msg)
