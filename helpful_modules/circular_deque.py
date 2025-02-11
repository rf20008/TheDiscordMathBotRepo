"""
This code is inspired by ChatGPT!
Copyright © 2025-present Samuel Guo
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - ConstantsLoader

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import typing


class CircularDequeIterator:
    """
    Iterator class for CircularDeque to iterate over its elements.

    Attributes:
        deque (CircularDeque): The CircularDeque instance being iterated.
        index (int): The current index in the deque.
    """
    index: int
    deque: "CircularDeque"
    def __init__(self, deque: "CircularDeque"):
        """
        Initializes the iterator with the deque to iterate over.

        Args:
            deque (CircularDeque): The deque instance to iterate over.
        """
        self.deque = deque
        self.index = 0
    def __iter__(self):
        """
        Returns the iterator object.

        Returns:
            CircularDequeIterator: The iterator object for the deque.
        """
        return self
    def advance(self, steps: int = 1):
        """
        Advances the iterator by a specified number of steps.

        Args:
            steps (int, optional): The number of steps to advance. Defaults to 1.
        """
        self.index += steps
    def __next__(self) -> typing.Any:
        """
        Returns the next element in the deque.

        Returns:
            Any: The next element in the deque.

        Raises:
            StopIteration: If the iterator reaches the end of the deque.
        """
        if self.index >= len(self.deque):
            raise StopIteration
        val = self.deque[self.index]
        self.advance()
        return val


class CircularDeque:
    """
    A circular deque (double-ended queue) implementation with dynamic resizing.

    Attributes:
        size (int): The current number of elements in the deque.
        front (int): The index of the front of the deque.
        back (int): The index of the back of the deque.
        data (list): The underlying list storing the deque elements.
    """
    size: int
    front: int
    back: int
    data: list
    @property
    def capacity(self) -> int:
        """
        Returns the capacity of the deque (size of the underlying list).

        Returns:
            int: The capacity of the deque.
        """
        return len(self.data)

    def __init__(self, iterable=None):
        """
        Initializes the deque with an iterable or an empty deque.

        Args:
            iterable (iterable, optional): The iterable to initialize the deque with. Defaults to an empty deque.
        """
        if iterable is None:
            iterable = []
        self.data = list(iterable)
        self.front = 0
        self.back = self.capacity - 1
        self.size = self.capacity
    def __getitem__(self, item) -> typing.Any:
        """
        Retrieves an element by index or slice.

        Args:
            item (int or slice): The index or slice to retrieve from the deque.

        Returns:
            Any or list: The element(s) at the specified index or slice.

        Raises:
            TypeError: If the index is not an integer or slice.
            IndexError: If the index is out of range.
        """
        if not isinstance(item, int) and not isinstance(item, slice): # make sure it's a index
            raise TypeError(f"CircularDeque indices must be integers or slices, not {item.__class__.__name__}")
        if isinstance(item, slice): # slcie logic
            data = []
            for i in range(item.start, item.stop, item.step): # append manually
                data.append(self[i])
            return data
        if item >= self.size or item < - self.size: # make sure index in range
            raise IndexError("CircularDeque index out of range")
        if item>=0:
            return self.data[(self.front + item)%self.capacity]
        return self.data[(self.back - item)%self.capacity]
    def __setitem__(self, index, value):
        """
         Sets an element at a specific index or slice.

         Args:
             index (int or slice): The index or slice to set.
             value (Any or list): The value to set at the specified index or slice.

         Raises:
             TypeError: If the index is not an integer or slice.
             IndexError: If the index is out of range.
             ValueError: If the length of the slice doesn't match the value.
         """
        if not isinstance(index, int) and not isinstance(index, slice):
            raise TypeError(f"CircularDeque indices must be integers or slices, not {index.__class__.__name__}")
        if isinstance(index, slice):
            start = index.start or 0
            stop = index.stop or self.size
            step = index.step or 1
            if start < 0 or stop > self.capacity or start >= self.capacity:
                raise IndexError("Slice indices are out of range")
            R = range(start, stop, step)
            if len(R) != len(value):
                raise ValueError("The length of the slice must be equal to the length of the value")
            for v, i in zip(R, value):
                if i >= self.size or i < - self.size:
                    raise IndexError("CircularDeque index out of range")
                self.data[(self.front + i)%self.capacity] = v
        else:
            self.data[(self.front + index)%self.capacity] = value
    @property
    def left(self) -> typing.Any:
        """
        Retrieves the leftmost element (front of the deque).

        Returns:
            Any: The leftmost element.

        Raises:
            IndexError: If the deque is empty.
        """
        if self.size == 0:
            raise IndexError("Empty CircularDeque has no left()")
        return self.data[self.front]
    @property
    def right(self):
        """
        Retrieves the rightmost element (back of the deque).

        Returns:
            Any: The rightmost element.

        Raises:
            IndexError: If the deque is empty.
        """
        if self.size == 0:
            raise IndexError("Empty CircularDeque has no right()")
        return self.data[(self.back-1)%self.capacity]

    def __len__(self):
        """
        Returns the number of elements in the deque.

        Returns:
            int: The size of the deque.
        """
        return self.size

    def resize(self, new_size, allow_data_loss = False):
        """
        Resizes the deque to a new size.

        Args:
            new_size (int): The new size of the deque.
            allow_data_loss (bool, optional): If False, prevents data loss during resizing. Defaults to False.

        Raises:
            ValueError: If resizing would result in data loss and allow_data_loss is False.
        """
        if len(self) < new_size and not allow_data_loss:
            raise ValueError("Data would be lost by this resize!")
        old_size = min(self.size, new_size)
        new_data = [None for _ in range(new_size)]
        for i in range(old_size):
            new_data[i] = self.data[(self.front + i)%self.capacity]
        self.data = new_data
        self.front = 0
        self.back = old_size

    def __iter__(self):
        """
        Returns an iterator for the deque.

        Returns:
            CircularDequeIterator: The iterator for the deque.
        """
        return CircularDequeIterator(self)

    def __mul__(self, other):
        """
        Multiplies the deque by an integer, repeating its elements.

        Args:
            other (int): The number of times to repeat the deque.

        Returns:
            CircularDeque: A new deque containing the repeated elements.

        Raises:
            ValueError: If the multiplication value is negative.
            TypeError: If the operand is not an integer.
        """
        if isinstance(other, int):
            # Case 1: Multiplying deque by an integer (repeating the deque)
            if other < 0:
                raise ValueError("Multiplication by a negative number is not supported.")

            new_deque = CircularDeque()  # Create a new deque to store the result
            for _ in range(other):
                # Add the current deque to the new deque `other` times
                new_deque.extend_right(self)  # Assuming extend_right appends the entire deque

            return new_deque
        else:
            raise TypeError("Unsupported operand type(s) for *: 'CircularDeque' and '{}'".format(type(other).__name__))
    def __rmul__(self, other):
        """
        Reverse multiplication operation for the deque.

        Args:
            other (int): The number of times to repeat the deque.

        Returns:
            CircularDeque: A new deque containing the repeated elements.
        """
        return self.__mul__(self, other)
    def __lt__(self, other):
        """
        Compares the deque with another deque for less-than relation.

        Args:
            other (CircularDeque): The other deque to compare with.

        Returns:
            bool: True if this deque is smaller, False otherwise.

        Raises:
            TypeError: If the operand is not an instance of CircularDeque.
        """
        for a, b in zip(self, other):
            if a != b:
                return a<b
        return len(self) < len(other)
    def __eq__(self, other):
        """
        Checks whether this deque is equal to another deque.

        Args:
            other (CircularDeque): The other deque to compare with.

        Returns:
            bool: True if this deque is equal to the other deque, False otherwise.

        """
        if not isinstance(other, type(self)):
            return False
        if len(self) != len(other):
            return False
        for a,b in zip(self, other):
            if a != b:
                return False
        return True

    def __le__(self, other):
        """
        Compares the deque with another deque for less-than or equal to relation.

        Args:
            other (CircularDeque): The other deque to compare with.

        Returns:
            bool: True if this deque is less than or equal to the other deque, False otherwise.

        Raises:
            TypeError: If the operand is not an instance of CircularDeque.
        """
        for a, b in zip(self, other):
            if a != b:
                return a < b
        return len(self) <= len(other)
    def __gt__(self, other):
        """
        Compares the deque with another deque for greater-than relation.

        Args:
            other (CircularDeque): The other deque to compare with.

        Returns:
            bool: True if this deque is larger, False otherwise.

        Raises:
            TypeError: If the operand is not an instance of CircularDeque.
        """
        for a, b in zip(self, other):
            if a != b:
                return a>b
        return len(self) > len(other)
    def __ge__(self, other):
        """
        Compares the deque with another deque for greater-than or equal to relation.

        Args:
            other (CircularDeque): The other deque to compare with.

        Returns:
            bool: True if this deque is greater than or equal to the other deque, False otherwise.

        Raises:
            TypeError: If the operand is not an instance of CircularDeque.
        """
        for a, b in zip(self, other):
            if a != b:
                return a > b
        return len(self) >= len(other)
    def append_left(self, item):
        """
        Adds an item to the front (left) of the deque.

        Args:
            item: The item to add to the deque.

        If the deque is full, the capacity is doubled before adding the item.
        """
        if len(self)==self.capacity:
            self.resize(self.size*2 + 1)
        self.size += 1
        self.front = (self.front - 1)%self.capacity
        self.data[self.front] = item

    def append_right(self, item):
        """
        Adds an item to the back (right) of the deque.

        Args:
            item: The item to add to the deque.

        If the deque is full, the capacity is doubled before adding the item.
        """
        if len(self) == self.capacity:
            self.resize(self.size * 2 + 1)

        self.size += 1
        self.back = (self.back+1)%self.capacity
        self.data[self.back - 1] = item
    def extend_right(self, items):
        """
        Adds multiple items to the back (right) of the deque.

        Args:
            items (iterable): The items to add to the deque.

        If the deque does not have enough capacity, the size is adjusted before adding the items.
        """
        if len(self) + len(items) >= self.capacity:
            self.resize((self.size + len(items))*2 + 1)
        for val in items:
            self.data[self.back] = val  # Store at back (which is exclusive, i.e., the next free slot)
            self.back = (self.back + 1) % self.capacity  # Move back pointer to the next free slot
            self.size += 1
    def extend_left(self, items, reverse=True):
        """
        Adds multiple items to the front (left) of the deque.

        Args:
            items (iterable): The items to add to the deque.
            reverse (bool): If True, the items are added in reverse order. Defaults to True.

        If the deque does not have enough capacity, the size is adjusted before adding the items.
        """
        if len(self) + len(items) >= self.capacity:
            self.resize((self.size + len(items))*2 + 1)
        vitems = reversed(items) if reverse else items
        for val in vitems:
            self.data[(self.front - 1) % self.capacity] = val  # Store at back (which is exclusive, i.e., the next free slot)
            self.front = (self.front - 1) % self.capacity  # Move front pointer to the next free slot
            self.size += 1
    def append(self, item):
        """
        Adds an item to the back (right) of the deque.

        Args:
            item: The item to add to the deque.
        """
        self.append_right(item)
    def pop_left(self):
        """
        Removes and returns the item from the front (left) of the deque.

        Returns:
            The item removed from the front.

        Raises:
            ValueError: If the deque is empty.

        If the deque's size falls below a threshold, the capacity is reduced.
        """
        if len(self)==0:
            raise ValueError("Cannot pop from an empty CircularDeque")
        if len(self) < self.capacity//5:
            self.resize(self.size//2 + 1)

        val = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front+1)%self.capacity
        self.size -= 1
        return val

    def pop_right(self):
        """
        Removes and returns the item from the back (right) of the deque.

        Returns:
            The item removed from the back.

        Raises:
            ValueError: If the deque is empty.

        If the deque's size falls below a threshold, the capacity is reduced.
        """
        if len(self) == 0:
            raise ValueError("Cannot pop from an empty CircularDeque")
        if len(self) < self.capacity // 5:
            self.resize(self.size // 2 + 1)

        val = self.data[(self.back-1)%self.capacity]
        self.data[(self.back-1)%self.capacity] = None
        self.back = (self.back -1) % self.capacity
        self.size -= 1
        return val
    def index(self, x, start=0, end = -1):
        if end == -1:
            end = self.size
        for i in range(start, end):
            if self[i] == x:
                return i
        return -1
    def count(self, x):
        occurrences = 0
        for item in self:
            if item==x:
                occurrences += 1
        return occurrences
    def __max__(self):
        if len(self)==0:
            raise ValueError("Empty CircularDeque has no max()")
        cur_max = self[0]
        for i in range(1, self.size):
            cur_max = max(cur_max, self[i])
        return cur_max
    def __min__(self):
        if len(self) == 0:
            raise ValueError("Empty CircularDeque has no min()")
        cur_min = self[0]
        for i in range(1, self.size):
            cur_min = min(cur_min, self[i])
        return cur_min
    def __sum__(self, start = 0):
        ssum = start
        for item in self:
            ssum += item
        return ssum

    def __sort__(self, key=None, reverse=False):
        flattened = list(self)
        flattened.sort(key=key, reverse=reverse)
        for i, val in zip(range(self.size), flattened):
            self[i] = val

    def sorted(self, key=None, reverse=False):
        return sorted(list(self), key=key, reverse=reverse)

    def insert(self, index, item):
        if index < 0 or index > self.size:
            raise IndexError('Index out of range')
        if self.size == self.capacity:
            self.resize(self.capacity * 2)

        # Shift elements to the right from the index
        for i in range(self.size, index, -1):
            self.data[(self.front + i) % self.capacity] = self.data[(self.front + i - 1) % self.capacity]

        # Insert the item at the given index
        insert_index = (self.front + index) % self.capacity
        self.data[insert_index] = item
        self.size += 1

    def remove(self, value):
        for i in range(self.size):
            actual_index = (self.front + i) % self.capacity
            if self.data[actual_index] == value:
                # Shift elements to the left from the index
                for j in range(i, self.size - 1):
                    self.data[(self.front + j) % self.capacity] = self.data[(self.front + j + 1) % self.capacity]
                self.size -= 1
                self.data[(self.front + self.size) % self.capacity] = None  # Clear the last element
                return value
        raise ValueError(f'{value} not found in deque')

    def __delitem__(self, index):
        if index < 0 or index >= self.size:
            raise IndexError('Index out of range')

        # Shift elements to the left from the index
        for i in range(index, self.size - 1):
            self.data[(self.front + i) % self.capacity] = self.data[(self.front + i + 1) % self.capacity]
        self.size -= 1
        self.data[(self.front + self.size) % self.capacity] = None  # Clear the last element
    def empty(self):
        return self.size() == 0