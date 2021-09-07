"""Callback we can use with the ansible client."""

from typing import Dict, Any, Iterator, Tuple
from enum import Enum

from ansible.plugins.callback import CallbackBase


class ResultStatus(Enum):
    """Result status string as an enum."""

    OK = "ok"
    UNREACHABLE = "unreachable"
    FAILED = "failed"


# Yes this is a struct.  No I am not sorry.
# pylint: disable=too-few-public-methods
class Result:
    """An ansible result from a results callback."""

    def __init__(self, status: ResultStatus, host: str, result: Dict[str, Any], *args, **kwargs):
        """Parametrize from a result Dict."""
        self.status: ResultStatus = status
        self.host: str = host
        self.result: Dict[str, Any] = result
        self.args: Tuple[Any] = args
        self.kwargs: Dict[str, Any] = kwargs


class ResultsCallback(CallbackBase):
    """A sample callback plugin used for collecting results as they come in."""

    def __init__(self, *args, **kwargs):
        """Initialize a results set."""
        super().__init__(*args, **kwargs)
        self._results: Dict[str, Result] = {}
        """Per host ResultStatus for an operation."""

    def __len__(self) -> int:
        """Return how many results we have.

        Returns:
        --------
        Integer number or results received.

        """
        return len(self._results)

    def __getitem__(self, host: str) -> Result:
        """Subscribe to a result using host name.

        Parameters:
        -----------
        hots (str) : Hostname.

        Returns:
        --------
        A Result object for the passed host name.

        Raises:
        -------
        Will raise a KeyError if the instance_id does not exist in the set.

        """
        return self._results[host]

    def __iter__(self) -> Iterator[Result]:
        """Create an iterator for the fixtures object.

        @TODO switch to just using a generator?

        Returns:
        --------
        An Iterator of Fixture objects

        """
        # Iterate across the to_list() set, as it is sorted.
        return iter(self._results.values())

    def __reversed__(self) -> Iterator[Result]:
        """Create a reversed iterator for the results.

        @TODO switch to just using a generator?

        Returns:
        --------
        An Iterator of Result objects

        """
        # Iterate across the to_list() set, as it is sorted.
        return reversed(self._results.values())

    # ANSIBLE CALLBACK FUNCTIONALITY
    #
    # The following methods are called by the ansible queue manager strategy object while the queue
    # is being processed.  Here we just try to catch information to produce discoverable results
    # in the object.
    #

    # need to access result _result in order to get info out of it.
    # pylint: disable=protected-access

    def v2_runner_on_unreachable(self, result):
        """Register and unreachable runner."""
        self._results[result._host.get_name()] = Result(
            status=ResultStatus.UNREACHABLE,
            host=result._host,
            result=result._result,
        )

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Register an OK runner."""
        self._results[result._host.get_name()] = Result(
            status=ResultStatus.OK, host=result._host, result=result._result, *args, **kwargs
        )

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """Register a failed runner."""
        self._results[result._host.get_name()] = Result(
            status=ResultStatus.FAILED, host=result._host, result=result._result, *args, **kwargs
        )
