import inspect
import weakref
import asyncio

from typing import Callable, Optional, Any
from asyncio import Lock

from app.core.utils import func_accepts_kwargs, Symbol
from app.core.config import settings


def _make_id(target: Any) -> int | tuple[int, int]:
    """
    Generate a unique identifier for the given target.

    :param target: The target object, which can be a method or any other callable.
    :return: A unique identifier for the target.
    """
    if inspect.ismethod(target):
        return id(target.__self__), id(target.__func__)

    return id(target)


NONE_ID = _make_id(None)
NO_RECEIVERS = Symbol("NO_RECEIVERS")


class Signal:
    """
    A class for creating and managing signals, allowing for asynchronous
    communication between different parts of an application.
    """

    def __init__(self, use_caching: bool = False):
        """
        Initialize the Signal instance.

        :param use_caching: Optional; If True, cache the receivers for each sender.
        """
        self.receivers: list[tuple[tuple[Any, Any], Callable]] = []
        self.lock: Lock = Lock()
        self.use_caching: bool = use_caching
        self.sender_receivers_cache: weakref.WeakKeyDictionary | dict = (
            weakref.WeakKeyDictionary() if use_caching else {}
        )
        self._dead_receivers: bool = False

    async def connect(
        self,
        receiver: Callable,
        sender: Optional[Any] = None,
        weak: bool = True,
        dispatch_uid: Optional[Any] = None,
    ) -> None:
        """
        Connect receiver to sender for signal.

        :param receiver: A function or an instance method which is to
        receive signals. Receivers must be hashable objects.
        If weak is True, then receiver must be weak referencable.
        Receivers must be able to accept keyword arguments.
        If a receiver is connected with a dispatch_uid argument, it
        will not be added if another receiver was already connected
        with that dispatch_uid.
        :param sender: The sender to which the receiver should respond.
        Must either bea Python object, or None to receive events from any sender.
        :param weak: Whether to use weak references to the receiver. By default, the
        module will attempt to use weak references to the receiver
        objects. If this parameter is false, then strong references will
        be used.
        :param dispatch_uid: An identifier used to uniquely identify
        a particular instance of a receiver. This will usually be a
        string, though it may be anything hashable.
        """

        # If this is a development environment:
        if settings.ENVIRONMENT == "local":
            if not callable(receiver):
                raise TypeError("Signal receivers must be callable.")
            # Check for **kwargs
            if not func_accepts_kwargs(receiver):
                raise ValueError(
                    "Signal receivers must accept keyword arguments (**kwargs)."
                )

        if dispatch_uid:
            lookup_key = (dispatch_uid, _make_id(sender))
        else:
            lookup_key = (_make_id(receiver), _make_id(sender))

        if weak:
            ref = weakref.ref
            receiver_object = receiver

            # Check for bound methods
            if inspect.ismethod(receiver):
                ref = weakref.WeakMethod
                receiver_object = receiver.__self__

            receiver = ref(receiver)
            weakref.finalize(receiver_object, self._remove_receiver)

        async with self.lock:
            self._clear_dead_receivers()

            if not any(_lookup_key == lookup_key for _lookup_key, _ in self.receivers):
                self.receivers.append((lookup_key, receiver))

            self.sender_receivers_cache.clear()

    async def disconnect(
        self,
        receiver: Optional[Callable] = None,
        sender: Optional[Any] = None,
        dispatch_uid: Optional[Any] = None,
    ) -> bool:
        """
        Disconnect receiver from sender for signal.

        If weak references are used, disconnect need not be called. The receiver
        will be removed from dispatch automatically.

        :param receiver: The registered receiver to disconnect. May be none if
        dispatch_uid is specified.
        :param sender: The registered sender to disconnect
        :param dispatch_uid: The unique identifier of the receiver to disconnect.
        :return: True if the receiver was successfully disconnected, False otherwise.
        """
        if dispatch_uid:
            lookup_key = (dispatch_uid, _make_id(sender))
        else:
            lookup_key = (_make_id(receiver), _make_id(sender))

        disconnected = False

        async with self.lock:
            self._clear_dead_receivers()

            for idx, (_lookup_key, _) in enumerate(self.receivers):
                if _lookup_key == lookup_key:
                    disconnected = True
                    del self.receivers[idx]
                    break

            self.sender_receivers_cache.clear()

        return disconnected

    async def send(self, sender: Any, **kwargs: Any) -> list[tuple[Callable, Any]]:
        """
        Send signal from sender to all connected receivers catching errors.

        :param sender: The sender of the signal. Can be any Python object (normally one
        registered with a "connect" method if you actually want something to occur).
        :param kwargs: Additional keyword arguments to pass to the receivers.
        :return: A list of tuple pairs [(receiver, response), ... ].
        If any receiver raises an error (specifically any subclass of
        Exception), return the error instance as the result for that receiver.
        """
        if (
            not self.receivers
            or self.sender_receivers_cache.get(sender) is NO_RECEIVERS
        ):
            return []

        receivers = await self._live_receivers(sender)

        responses = await asyncio.gather(
            *[receiver(sender=sender, signal=self, **kwargs) for receiver in receivers],
            return_exceptions=True
        )

        return list(zip(receivers, responses))

    async def has_listeners(self, sender: Optional[Any] = None) -> bool:
        """
        Check if there are any receivers connected to the signal.

        :param sender: Optional; The sender to check for connected receivers.
        :return: True if there are connected receivers, False otherwise.
        """
        return bool(await self._live_receivers(sender))

    def _clear_dead_receivers(self):
        # Note: caller is assumed to hold self.lock.
        if self._dead_receivers:
            self.receivers = [
                receiver
                for receiver in self.receivers
                if not (
                    isinstance(receiver[1], weakref.ReferenceType)
                    and receiver[1]() is None
                )
            ]
            self._dead_receivers = False

    async def _live_receivers(self, sender: Optional[Any]) -> list[Callable]:
        """
        Filter sequence of receivers to get resolved, live receivers.

        This checks for weak references and resolves them, then returning only
        live receivers.

        :param sender: The sender to retrieve receivers for.
        :return: A list of callable receivers.
        """
        receivers = None

        if self.use_caching and not self._dead_receivers:
            receivers = self.sender_receivers_cache.get(sender)
            # We could end up here with NO_RECEIVERS even if we do check this case in
            # .send() prior to calling _live_receivers() due to concurrent .send() call.
            if receivers is NO_RECEIVERS:
                return []

        if receivers is None:
            async with self.lock:
                self._clear_dead_receivers()

                sender_key = _make_id(sender)
                receivers = []

                for (_, _sender_key), receiver in self.receivers:
                    if _sender_key == NONE_ID or _sender_key == sender_key:
                        receivers.append(receiver)

                if self.use_caching:
                    if not receivers:
                        self.sender_receivers_cache[sender] = NO_RECEIVERS
                    else:
                        self.sender_receivers_cache[sender] = receivers

        non_weak_receivers = []

        for receiver in receivers:
            if isinstance(receiver, weakref.ReferenceType):
                # Dereference the weak reference.
                receiver = receiver()
                if receiver is not None:
                    non_weak_receivers.append(receiver)
            else:
                non_weak_receivers.append(receiver)

        return non_weak_receivers

    def _remove_receiver(self):
        self._dead_receivers = True
