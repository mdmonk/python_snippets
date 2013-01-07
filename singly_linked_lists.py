#!/usr/bin/python
"""Some experiments with singly-linked lists.

See the discussion: <http://www.orkut.com/CommMsgs.aspx?cmm=22317&tid=93968>

Give it a spin:

>>> import singly_linked_lists
>>> sll = makeSinglyLinkedList([1, 2, 3, 4, 5])
>>> printForward(sll)
>>> printReverseWithModification(sll)
>>> printReverseWithoutModification(sll)
>>> sll = reverseList(sll)

$Id$"""

def printForward(sll):
    """Prints a singly-linked list."""
    curPointer = sll
    while curPointer is not None:
        print(curPointer.data)
        curPointer = curPointer.next

def reverseList(sll):
    """Reverses a singly-linked list in-place, returning the new head.

    Usage:
    >>> sll = reverseList(sll)"""
    p = None
    q = sll
    while q is not None:
        r = q.next
        q.next = p
        p = q
        q = r
    return p

def printReverseWithModification(sll):
    """Prints a singly-linked list in reverse with Theta(n) time and Theta(1)
    memory.

    The list is reversed during the printing. It's reverted by the end,
    but other threads should not be playing with the list during this time."""
    sll = reverseList(sll)
    # printForward(sll)
    # Use our own print loop so we can re-reverse the list at the same time.
    p = None
    q = sll
    while q is not None:
        print(q.data)
        q_next = q.next
        q.next = p
        p = q
        q = q_next

def printReverseWithoutModification(sll):
    """Prints a singly-linked list in reverse with Theta(n^2) time and Theta(1)
    memory, without modifying the list."""

    # Learn the number of elements in the list.
    p = sll
    n = 0
    while p is not None:
        n = n + 1
        p = p.next

    for i in range(n-1, -1, -1):
        p = sll
        for j in range(0, i):
            p = p.next
        print(p.data)

def makeSinglyLinkedList(seq):
    """Makes a singly-linked list from a Python sequence."""
    class Node: pass
    sll = None
    cur = None
    for elem in seq:
        new = Node()
        new.next = None
        new.data = elem
        if cur is None:
            sll = new
        else:
            cur.next = new
        cur = new
    return sll
