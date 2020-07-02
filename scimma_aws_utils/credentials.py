import dataclasses
import datetime
import os
import json


@dataclasses.dataclass
class CredentialSet:
    version: int
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime.datetime

    def to_aws_creds(self):
        return {
            "Version": self.version,
            "AccessKeyId": self.access_key_id,
            "SecretAccessKey": self.secret_access_key,
            "SessionToken": self.session_token,
            "Expiration": self.expiration.isoformat()
        }

    def to_cache_file(self, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        json_data = self.to_aws_creds()
        with open(filename, "w") as f:
            json.dump(json_data, f)

    @classmethod
    def from_aws_creds(cls, creds):
        try:
            expiration = datetime.datetime.fromisoformat(creds["Expiration"])
        except TypeError:
            expiration = creds["Expiration"]
        return CredentialSet(
            version=1,
            access_key_id=creds["AccessKeyId"],
            secret_access_key=creds["SecretAccessKey"],
            session_token=creds["SessionToken"],
            expiration=expiration,
        )

    @classmethod
    def from_cache_file(cls, filename):
        with open(filename, "r") as f:
            json_data = json.load(f)
            return CredentialSet.from_aws_creds(json_data)

    def expired(self, margin=datetime.timedelta(minutes=10)):
        return datetime.datetime.now(self.expiration.tzinfo) > (self.expiration - margin)
