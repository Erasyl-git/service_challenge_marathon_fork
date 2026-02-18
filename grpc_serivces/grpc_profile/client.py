
import os
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, project_root)

profile_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.insert(0, profile_pkg)



import grpc
import profile_pb2
import profile_pb2_grpc
from rest_framework.exceptions import NotFound
from typing import Dict, Union



class ProfileInfo:
    def __init__(self):
        channel = grpc.insecure_channel("178.88.115.139:50052") #service_profiles #178.88.115.139
        self.stub = profile_pb2_grpc.ProfileStub(channel)

    def get_profile(self, user_id: int):
        try:
            request = profile_pb2.UserID(user_id=user_id)
            return self.stub.DataProfile(request)
        except grpc.RpcError as e:
            print("dd")
            print("gRPC error:", e)
            return None


# s = ProfileInfo()

# print(s.get_profile(1))

