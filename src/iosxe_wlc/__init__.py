from logging_handler import create_logger, INFO
import requests
import urllib
from time import time



class IosXeWlc:
    ''' Class to represent a Cisco IOS-XE based WLC (i.e. Cat 9800) '''
    def __init__(self, host:str, username:str, password:str, ca_cert:str|None=None, log_level=INFO):
        self.host, self.username, self.__password, self.ca_cert = host, username, password, ca_cert
        self.timeout, self.retry = 5, 3
        self._logger = create_logger(log_level, name=f'IOS-XE-WLC({host})')

    def update_creds(self, username:str, password:str):
        ''' Update the credentials '''
        self._logger.debug(f"Updating credentials. Username: {username}")
        self.username, self.__password = username, password

    def test(self) -> bool:
        ''' Test access to the IOS-XE WLC using the provided credentials '''
        self._logger.debug("Starting test...")
        for try_number in range(self.retry):
            try:
                start_time = time()
                response = requests.get(url=f"https://{self.host}/restconf/",
                                        auth=(self.username, self.__password),
                                        timeout=self.timeout,
                                        verify=self.ca_cert if self.ca_cert is not None else True,
                                        headers={'accept': 'application/yang-data+json'})
                response_time = time() - start_time
                if response.status_code == 200:
                    self._logger.info(f"Test successful. Status code: {response.status_code}. Try {try_number + 1}, response time: {response_time}")
                    return True
                self._logger.warning(f"Test {try_number + 1} failed. Try {try_number + 1}, Status code: {response.status_code}. Response time: {response_time}")
            except Exception as e:
                self._logger.warning(f"Test {try_number + 1} failed. Try {try_number + 1}, Error: {e.__class__.__name__}: {e}")
        self._logger.error(f"Test Failed! Tried {self.retry + 1 } times. Timeout is {self.timeout}. Check credentials and host and try again.")
        return False

    def get_clients(self, client:str|None=None, get_ip_info:bool=True) -> list:
        ''' Get all clients, or a specified client (client specified by MAC address) '''
        if client is not None:
            client = client.replace(':', '').replace('-', '').replace('.', '').lower()
            if len(client) != 12:
                raise ValueError(f"Expecting a client MAC address with 12 characters and got {client}")
            for character in client:
                if character not in ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']:
                    raise ValueError(f"Expecting MAC address and got an invalid char ({character}) {client}")
            client = f"{client[0:2]}:{client[2:4]}:{client[4:6]}:{client[6:8]}:{client[8:10]}:{client[10:12]}"
        self._logger.debug(f"Starting GET_CLIENTS for {'all users' if client is None else client}...")
        for try_number in range(self.retry):
            try:
                start_time = time()
                response = requests.get(url=f"https://{self.host}/restconf/data/Cisco-IOS-XE-wireless-client-oper:client-oper-data/common-oper-data" + ('' if client is None else f"={client}"),
                                        auth=(self.username, self.__password),
                                        timeout=self.timeout,
                                        verify=self.ca_cert if self.ca_cert is not None else True,
                                        headers={'accept': 'application/yang-data+json'})
                response_time = time() - start_time
                if response.status_code == 200:
                    client_list =  response.json().get('Cisco-IOS-XE-wireless-client-oper:common-oper-data', [])
                    self._logger.debug(f"GET_CLIENTS successful for {'all users' if client is None else client}. Returned {len(client_list)} clients. Status code: {response.status_code}. Try {try_number + 1}, response time: {response_time}")
                    if get_ip_info:
                        # get client IP info
                        for client_obj in client_list:
                            client_obj['ip_addr'] = self.get_client_addresses(client_obj['client-mac'])
                    return client_list
                self._logger.warning(f"GET_CLIENTS failed for {'all users' if client is None else client}. Status code: {response.status_code}. Try {try_number + 1}, response time: {response_time}")
            except Exception as e:
                self._logger.warning(f"GET_CLIENTS failed for {'all users' if client is None else client}. Error: {e.__class__.__name__}: {e}")
        self._logger.error(f"GET_CLIENTS Failed! Tried {self.retry + 1 } times. Timeout is {self.timeout}. Check credentials and host and try again.")
        return []

    def get_client_addresses(self, client:str|None=None) -> list:
        ''' return a list of the SISF database for all clients or a specific client '''
        if client is not None:
            client = client.replace(':', '').replace('-', '').replace('.', '').lower()
            if len(client) != 12:
                raise ValueError(f"Expecting a client MAC address with 12 characters and got {client}")
            for character in client:
                if character not in ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']:
                    raise ValueError(f"Expecting MAC address and got an invalid char ({character}) {client}")
            client = f"{client[0:2]}:{client[2:4]}:{client[4:6]}:{client[6:8]}:{client[8:10]}:{client[10:12]}"
        self._logger.debug(f"Starting GET_CLIENT_ADDRESSES for {'all users' if client is None else client}...")
        for try_number in range(self.retry):
            try:
                start_time = time()
                response = requests.get(url=f"https://{self.host}/restconf/data/Cisco-IOS-XE-wireless-client-oper:client-oper-data/sisf-db-mac" + ('' if client is None else f"={client}"),
                                        auth=(self.username, self.__password),
                                        timeout=self.timeout,
                                        verify=self.ca_cert if self.ca_cert is not None else True,
                                        headers={'accept': 'application/yang-data+json'})
                response_time = time() - start_time
                if response.status_code == 200:
                    client_list =  response.json().get('Cisco-IOS-XE-wireless-client-oper:sisf-db-mac', [])
                    self._logger.debug(f"GET_CLIENT_ADDRESSES successful for {'all users' if client is None else client}. Returned {len(client_list)} clients. Status code: {response.status_code}. Try {try_number + 1}, response time: {response_time}")
                    return client_list
                self._logger.warning(f"GET_CLIENT_ADDRESSES failed for {'all users' if client is None else client}. Status code: {response.status_code}. Try {try_number + 1}, response time: {response_time}")
            except Exception as e:
                self._logger.warning(f"GET_CLIENT_ADDRESSES failed for {'all users' if client is None else client}. Error: {e.__class__.__name__}: {e}")
        self._logger.error(f"GET_CLIENT_ADDRESSES Failed! Tried {self.retry + 1 } times. Timeout is {self.timeout}. Check credentials and host and try again.")
        return []

