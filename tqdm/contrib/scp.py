"""
Providing a progress writer for scp.SCPClient
"""
from sys import stderr
from io import IOBase
import typing
from tqdm import tqdm

__author__ = {"github.com/": ["schwaneberg"]}
__all__ = ['ScpProgressWriter']


class ScpProgressWriter:
    """
    Implementing a ProgressWriter for SCPClient using tqdm

    Examples
    --------
    >>> from paramiko import SSHClient
    >>> from scp import SCPClient
    >>> from tqdm.contrib.scp import ScpProgressWriter
    >>> ssh = SSHClient()
    >>> ssh.load_system_host_keys()
    >>> ssh.connect('example.com')
    >>> # Providing a TQDM progress writer
    >>> with ScpProgressWriter() as pw:
    >>>     with SCPClient(ssh.get_transport(), progress4=pw) as scp:
    >>>         scp.put('archive.zip', '/tmp/archive.zip')
    >>>         scp.put('another_archive.zip', '/tmp/another_archive.zip')
    Copying archive.zip (peer: example.com): 100%|██████████| 15.4M/15.4M [00:07<00:00, 2.11MB/s]
    Copying another_archive.zip (peer: example.com): 100%|██████████| 42.9M/42.9M [00:18<00:00, 2.40MB/s]
    """
    def __init__(self, desc: typing.Optional[str] = None, min_file_size: int = 102400, file: IOBase = stderr):
        """
        Parameters
        ----------
        :param desc: Descriptive string
        :param min_file_size: Minimal amount of bytes to create a progress bar for
        :param file: Output file for tqdm
        """
        self.__progress = 0
        self.__desc = desc if desc is not None else "Copying"
        self.__tqdm = None
        self.__cur_file = None
        self.__file = file
        self.__min_file_size = min_file_size

    def __enter__(self):
        return self.update_to

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__tqdm is not None:
            self.__tqdm.close()

    def update_to(self, filename, size, sent, peername: typing.Optional[typing.Tuple[str, int]] = None):
        """
        Callback with compatible signature for SCP
        :param filename: filename - will be appended to the description
        :param size: total amount of bytes to transfer
        :param sent: transfered amount of bytes
        :param peername: Tuple of IP and port
        """
        if size > self.__min_file_size:
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", "backslashreplace")
            desc = f"{self.__desc} {filename} (peer: {peername[0]})" if peername else f"{self.__desc} {filename}"
            if filename != self.__cur_file:
                if self.__tqdm is not None:
                    self.__tqdm.close()
                    self.__progress = 0
                self.__cur_file = filename
                self.__tqdm = tqdm(file=self.__file,
                                   desc=desc,
                                   unit="B",
                                   unit_divisor=1024,
                                   unit_scale=True)
            self.__tqdm.total = size
            self.__tqdm.update(sent - self.__progress)
            self.__progress = sent
