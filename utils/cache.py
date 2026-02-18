import os
import redis
import json

from typing import Dict, Optional

from service_challenge_marathon.settings import DB, PORT, HOST

class CacheData:

    def __init__(self):
        self.broker = redis.StrictRedis(host=HOST, port=PORT, db=DB)

    def set_cache_source_data(self, source_name: str, data: Dict) -> Dict:

        self.broker.set(f"source: {source_name}", json.dumps(data), ex=3600)

        return self.get_cache_source_data(source_name)
    
    def get_cache_source_data(self, source_name: str) -> Optional[Dict]:

        raw = self.broker.get(f"source: {source_name}")

        if not raw:
            return None
        
        if isinstance(raw, (bytes, bytearray)):

            raw = raw.decode("utf-8")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None

        return data
    

    def delete_cache_source_data(self, source_name: str) -> None:
        
        self.broker.delete(f"source: {source_name}")



    


