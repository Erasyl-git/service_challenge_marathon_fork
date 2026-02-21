import os
import sys

challenge_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, challenge_root)

challenge_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.insert(0, challenge_pkg)

import grpc
import challenge_pb2
import challenge_pb2_grpc
from rest_framework.exceptions import NotFound
from typing import Dict, Union



class ChallengeInfo:

    def __init__(self) -> None:

        channel__ = grpc.insecure_channel("service_challange:50057")

        self.stub_ = challenge_pb2_grpc.ServiceChallengeStub(channel__)


    def get_challenge(self, id: int) -> Dict[str, str]:

        request = challenge_pb2.ResponseChallengeId(id=id)

        try:
            response = self.stub_.GetChallenges(request)

        except grpc.RpcError as e:
            raise ConnectionError("user not found or access challenge is not Found" + f"{e}")
        
        return response



